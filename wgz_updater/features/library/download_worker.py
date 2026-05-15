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
    return "drive.google.com" in url or "docs.google.com" in url


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

    # ── Google Drive API download (authenticated) ─────────────────

    def _run_drive_api(self) -> None:
        try:
            from googleapiclient.discovery import build
            from googleapiclient.http import MediaIoBaseDownload
            from ..auth.session import AuthSession
        except Exception as exc:
            log.warning("Drive API unavailable, falling back to gdown: %s", exc)
            self._run_gdown()
            return

        credentials = AuthSession.credentials()
        file_id = _extract_drive_id(self._url)

        try:
            self.status.emit("Đang kết nối Google Drive (xác thực)...")
            service = build("drive", "v3", credentials=credentials)

            meta = service.files().get(fileId=file_id, fields="name,size").execute()
            filename = meta.get("name", "download")
            total_bytes = int(meta.get("size", 0) or 0)

            dest = (
                self._dest_dir / self._file_hint if self._file_hint
                else self._dest_dir / filename
            )
            self._dest_dir.mkdir(parents=True, exist_ok=True)

            self.status.emit(f"Đang tải  {filename}...")
            request = service.files().get_media(fileId=file_id)

            t_last = time.monotonic()
            bytes_last = 0

            with open(dest, "wb") as fh:
                dl = MediaIoBaseDownload(fh, request, chunksize=8 * 1024 * 1024)
                done = False
                while not done:
                    if self._cancel:
                        self.failed.emit("Đã hủy")
                        return
                    status_obj, done = dl.next_chunk()
                    if status_obj:
                        pct = int(status_obj.progress() * 100)
                        self.progress.emit(pct)
                        now = time.monotonic()
                        elapsed = now - t_last
                        if elapsed >= 0.8:
                            cur = status_obj.resumable_progress
                            bps = (cur - bytes_last) / elapsed
                            self.speed.emit(_format_speed(bps))
                            t_last = now
                            bytes_last = cur

            self.progress.emit(100)
            self.finished_ok.emit(str(dest))

        except Exception as exc:
            log.exception("Drive API download failed")
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
