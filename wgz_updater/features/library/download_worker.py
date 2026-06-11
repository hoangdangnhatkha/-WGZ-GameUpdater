from __future__ import annotations

import io
import logging
import re
import sys
import time
from pathlib import Path

from PyQt6.QtCore import QThread, pyqtSignal

log = logging.getLogger(__name__)

_PERCENT_RE = re.compile(r"(\d{1,3})\s*%")
_SPEED_RE = re.compile(r"([\d\.]+)\s?([KMG]?B/s)")
_DRIVE_ID_RE = re.compile(r"/d/([^/?&]+)|[?&]id=([^&]+)")


def _is_drive_url(url: str) -> bool:
    # `drive.usercontent.google.com` is the direct-download CDN host that
    # Google now hands out for large public files; it carries the same
    # `?id=<fileId>` query param so the authenticated REST path applies.
    return (
        "drive.google.com" in url
        or "docs.google.com" in url
        or "drive.usercontent.google.com" in url
    )


def _ensure_token_fresh(credentials) -> bool:
    """Return True if the credentials are usable; refresh when expired.

    Refreshing requires `google.auth.transport.requests.Request`; we import
    it lazily so the dependency is paid only when an authenticated Drive
    download actually runs.
    """
    try:
        if credentials.valid:
            return True
    except Exception:
        return False

    try:
        from google.auth.transport.requests import Request
        credentials.refresh(Request())
        return bool(credentials.valid)
    except Exception:
        log.exception("Credentials refresh failed")
        return False


def _extract_drive_id(url: str) -> str:
    m = _DRIVE_ID_RE.search(url)
    if m:
        return m.group(1) or m.group(2)
    return url


def _format_speed(bps: float) -> str:
    if bps >= 1024 * 1024:
        return f"{bps / (1024 * 1024):.1f} MB/s"
    if bps >= 1024:
        return f"{bps / 1024:.1f} KB/s"
    return f"{bps:.0f} B/s"


class _GdownProgressTrap(io.TextIOBase):
    def __init__(self, on_percent, on_speed) -> None:
        super().__init__()
        self._on_percent = on_percent
        self._on_speed = on_speed

    def write(self, text: str) -> int:
        if not text:
            return 0
        m = _PERCENT_RE.search(text)
        if m:
            try:
                self._on_percent(int(m.group(1)))
            except Exception:
                pass
        s = _SPEED_RE.search(text)
        if s:
            try:
                self._on_speed(s.group(0))
            except Exception:
                pass
        return len(text)

    def flush(self) -> None:
        return None


class DownloadWorker(QThread):
    progress = pyqtSignal(int)       # 0..100
    speed = pyqtSignal(str)          # "12.3 MB/s"
    status = pyqtSignal(str)         # human-readable
    finished_ok = pyqtSignal(str)    # final path
    failed = pyqtSignal(str)         # error message

    def __init__(self, url: str, dest_dir: Path, file_hint: str = "", parent=None) -> None:
        super().__init__(parent)
        self._url = url
        self._dest_dir = Path(dest_dir)
        self._file_hint = file_hint
        self._cancel = False

    def cancel(self) -> None:
        self._cancel = True

    def run(self) -> None:
        try:
            from ..auth.session import AuthSession
            authenticated = AuthSession.is_authenticated()
        except Exception:
            authenticated = False

        if authenticated and _is_drive_url(self._url):
            self._run_drive_api()
        else:
            self._run_gdown()

    # ── Google Drive REST download (authenticated) ────────────────
    #
    # Direct HTTPS calls against the Drive v3 REST API via the shared
    # httpx client (HTTP/2, connection pool). Replaces googleapiclient
    # which dragged in ~97 MB of unused API discovery metadata.

    _DRIVE_API_BASE = "https://www.googleapis.com/drive/v3/files"
    _DOWNLOAD_CHUNK = 8 * 1024 * 1024

    # Stall detection: when sustained throughput drops below the threshold for
    # the configured window, close the current stream and reopen it with a
    # Range header. Drive sometimes hands the new TCP connection a fresh
    # throttle bucket — when it does we recover; when it doesn't we just
    # continue at the slow rate without burning more retries.
    _STALL_BPS = 500 * 1024          # 500 KB/s
    _STALL_WINDOW_S = 30.0
    _MAX_RECONNECTS = 4
    _BACKOFF_S = 2.0

    def _run_drive_api(self) -> None:
        try:
            from ..auth.session import AuthSession
            from ...core.http import client as http_client
        except Exception as exc:
            log.warning("Drive REST deps unavailable, falling back to gdown: %s", exc)
            self._run_gdown()
            return

        credentials = AuthSession.credentials()
        if credentials is None:
            log.info("No credentials in AuthSession, falling back to gdown")
            self._run_gdown()
            return

        # Refresh the token if it has expired. google-auth's Credentials object
        # exposes `.valid` and `.refresh(transport.Request)`; we only import the
        # transport when we actually need it to keep cold-startup cheap.
        if not _ensure_token_fresh(credentials):
            log.warning("Token refresh failed, falling back to gdown")
            self._run_gdown()
            return

        file_id = _extract_drive_id(self._url)
        if not file_id:
            self.failed.emit("Không trích xuất được Drive file ID")
            return

        headers = {"Authorization": f"Bearer {credentials.token}"}
        meta_url = (
            f"{self._DRIVE_API_BASE}/{file_id}"
            "?fields=name%2Csize&supportsAllDrives=true"
        )
        media_url = (
            f"{self._DRIVE_API_BASE}/{file_id}"
            "?alt=media&supportsAllDrives=true"
        )

        try:
            self.status.emit("Đang kết nối Google Drive (xác thực)...")
            client = http_client()

            meta_resp = client.get(meta_url, headers=headers)
            meta_resp.raise_for_status()
            meta = meta_resp.json()
            filename = meta.get("name", "download")
            total_bytes = int(meta.get("size", 0) or 0)

            dest = (
                self._dest_dir / self._file_hint if self._file_hint
                else self._dest_dir / filename
            )
            self._dest_dir.mkdir(parents=True, exist_ok=True)

            self.status.emit(f"Đang tải {filename}...")

            downloaded = 0
            reconnects = 0

            # Open the destination once; Range-resume seeks back to `downloaded`
            # on each reconnect attempt instead of restarting the file.
            with open(dest, "wb") as fh:
                while True:
                    if self._cancel:
                        self.failed.emit("Đã hủy")
                        return

                    range_headers = dict(headers)
                    if downloaded:
                        range_headers["Range"] = f"bytes={downloaded}-"

                    stalled = False
                    t_last = time.monotonic()
                    bytes_last = downloaded
                    stall_window_start = t_last
                    stall_window_bytes = downloaded

                    try:
                        with client.stream("GET", media_url, headers=range_headers) as resp:
                            # Server may ignore Range and serve 200 from byte 0
                            # (rare with Drive). Truncate and start over.
                            if downloaded and resp.status_code == 200:
                                log.info("Drive ignored Range header; restarting from 0")
                                fh.seek(0)
                                fh.truncate()
                                downloaded = 0
                                bytes_last = 0
                                stall_window_bytes = 0
                            elif resp.status_code not in (200, 206):
                                resp.raise_for_status()

                            for chunk in resp.iter_bytes(chunk_size=self._DOWNLOAD_CHUNK):
                                if self._cancel:
                                    self.failed.emit("Đã hủy")
                                    return
                                fh.write(chunk)
                                downloaded += len(chunk)
                                if total_bytes:
                                    pct = int(downloaded * 100 / total_bytes)
                                    self.progress.emit(pct)

                                now = time.monotonic()
                                elapsed = now - t_last
                                if elapsed >= 0.8:
                                    bps = (downloaded - bytes_last) / elapsed
                                    self.speed.emit(_format_speed(bps))
                                    t_last = now
                                    bytes_last = downloaded

                                # Sliding-window stall check.
                                win = now - stall_window_start
                                if win >= self._STALL_WINDOW_S:
                                    avg_bps = (downloaded - stall_window_bytes) / win
                                    if (
                                        avg_bps < self._STALL_BPS
                                        and reconnects < self._MAX_RECONNECTS
                                    ):
                                        stalled = True
                                        break
                                    stall_window_start = now
                                    stall_window_bytes = downloaded

                    except Exception as exc:
                        # Network blip / 5xx — treat as a stall and retry.
                        if reconnects >= self._MAX_RECONNECTS:
                            raise
                        log.warning("Drive stream error: %s — reconnecting", exc)
                        stalled = True

                    if not stalled:
                        break

                    reconnects += 1
                    self.status.emit(
                        f"Drive giới hạn tốc độ — đang kết nối lại "
                        f"(lần {reconnects}/{self._MAX_RECONNECTS})..."
                    )
                    log.info(
                        "Stall detected at %d bytes; reconnecting (attempt %d)",
                        downloaded, reconnects,
                    )
                    time.sleep(self._BACKOFF_S)

            self.progress.emit(100)
            self.finished_ok.emit(str(dest))

        except Exception as exc:
            log.exception("Drive REST download failed")
            self.failed.emit(str(exc))

    # ── gdown fallback (public/unauthenticated links) ─────────────

    def _run_gdown(self) -> None:
        try:
            import gdown
        except Exception as exc:
            self.failed.emit(f"gdown not available: {exc}")
            return

        self._dest_dir.mkdir(parents=True, exist_ok=True)
        if self._file_hint:
            out_path = str(self._dest_dir / self._file_hint)
        else:
            out_path = str(self._dest_dir) + "/"

        original_stderr = sys.stderr
        trap = _GdownProgressTrap(
            on_percent=lambda p: self.progress.emit(p),
            on_speed=lambda s: self.speed.emit(s),
        )
        sys.stderr = trap
        try:
            self.status.emit("Đang kết nối Google Drive...")
            result = gdown.download(self._url, out_path, quiet=False, fuzzy=True, resume=True)
            if self._cancel:
                self.failed.emit("Đã hủy")
                return
            if not result or not Path(result).exists():
                self.failed.emit("Tải thất bại")
                return
            self.progress.emit(100)
            self.finished_ok.emit(str(result))
        except Exception as exc:
            log.exception("gdown download failed")
            self.failed.emit(str(exc))
        finally:
            sys.stderr = original_stderr
