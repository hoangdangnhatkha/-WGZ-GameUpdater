from __future__ import annotations

import logging
import re
import shutil
import subprocess
import time
import zipfile
from pathlib import Path

from PyQt6.QtCore import QThread, pyqtSignal

from ...core.paths import PACKAGE_ROOT, UNRAR_EXE

log = logging.getLogger(__name__)

# 1 MB write buffer — Python's default 8 KB hammers the OS with syscalls and
# bottlenecks at 30-50 MB/s on SSD; 1 MB sustains 200+ MB/s.
_EXTRACT_BUF = 1 << 20

# Progress emit throttle. Cross-thread signal per file (or per chunk) saturates
# the Qt event loop on archives with tens of thousands of members; 5 Hz keeps
# the UI responsive while still feeling live.
_PROGRESS_HZ = 5
_PROGRESS_MIN_INTERVAL = 1.0 / _PROGRESS_HZ

_UNRAR_PERCENT_RE = re.compile(rb"(\d{1,3})%")


def _resolve_unrar() -> Path | None:
    candidates = [
        PACKAGE_ROOT / UNRAR_EXE,
        PACKAGE_ROOT.parent / UNRAR_EXE,
        Path.cwd() / UNRAR_EXE,
    ]
    for c in candidates:
        if c.exists():
            return c
    return None


class ExtractWorker(QThread):
    progress = pyqtSignal(int)
    status = pyqtSignal(str)
    finished_ok = pyqtSignal(str)
    failed = pyqtSignal(str)

    def __init__(
        self,
        archive_path: Path,
        target_dir: Path,
        archive_type: str,
        password: str | None = None,
        delete_before: list[str] | None = None,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._archive = Path(archive_path)
        self._target = Path(target_dir)
        self._type = archive_type.lower()
        self._password = password
        self._delete_before = list(delete_before or [])

    def run(self) -> None:
        try:
            self._target.mkdir(parents=True, exist_ok=True)
            self._purge_before()

            if self._type == "exe":
                self.status.emit("Đang chạy installer...")
                subprocess.Popen([str(self._archive)])
                self.progress.emit(100)
                self.finished_ok.emit(str(self._target))
                return

            if self._type == "zip":
                self._extract_zip()
            elif self._type == "rar":
                self._extract_rar()
            else:
                self.failed.emit(f"Loại tệp không hỗ trợ: {self._type}")
                return

            self.progress.emit(100)
            self.finished_ok.emit(str(self._target))
        except Exception as exc:
            log.exception("Extraction failed")
            self.failed.emit(str(exc))

    def _purge_before(self) -> None:
        for rel in self._delete_before:
            target = self._target / rel
            if target.exists():
                self.status.emit(f"Đang dọn dẹp: {rel}")
                if target.is_dir():
                    shutil.rmtree(target, ignore_errors=True)
                else:
                    try:
                        target.unlink()
                    except OSError:
                        pass

    def _extract_zip(self) -> None:
        self.status.emit("Đang giải nén ZIP...")
        target = self._target
        pwd_bytes = self._password.encode("utf-8") if self._password else None

        with zipfile.ZipFile(self._archive, "r") as zf:
            members = zf.infolist()
            total_bytes = sum(m.file_size for m in members) or 1
            done = 0
            last_pct = -1
            last_emit = time.monotonic()

            for m in members:
                # zipfile preserves forward-slash names; Path handles both.
                dest = target / m.filename
                if m.is_dir():
                    dest.mkdir(parents=True, exist_ok=True)
                    continue
                dest.parent.mkdir(parents=True, exist_ok=True)

                with zf.open(m, pwd=pwd_bytes) as src, \
                        open(dest, "wb", buffering=_EXTRACT_BUF) as out:
                    while True:
                        chunk = src.read(_EXTRACT_BUF)
                        if not chunk:
                            break
                        out.write(chunk)
                        done += len(chunk)

                        now = time.monotonic()
                        if now - last_emit >= _PROGRESS_MIN_INTERVAL:
                            pct = int(done * 100 / total_bytes)
                            if pct != last_pct:
                                self.progress.emit(pct)
                                last_pct = pct
                            last_emit = now

    def _extract_rar(self) -> None:
        unrar = _resolve_unrar()
        if not unrar:
            raise RuntimeError("UnRAR.exe not found")
        self.status.emit("Đang giải nén RAR...")
        cmd = [str(unrar), "x", "-y", "-o+"]
        if self._password:
            cmd.append(f"-p{self._password}")
        cmd.extend([str(self._archive), str(self._target) + "\\"])

        # Stream stdout so we can both expose progress (UnRAR prints `NN%`
        # updates inline) and avoid the multi-GB buffer growth that
        # `capture_output=True` causes on long extractions.
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            bufsize=0,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )

        last_pct = -1
        last_emit = time.monotonic()
        try:
            assert proc.stdout is not None
            while True:
                # UnRAR rewrites the percent in place using CR; read in modest
                # chunks rather than line-by-line so we don't block.
                buf = proc.stdout.read(256)
                if not buf:
                    break
                m = _UNRAR_PERCENT_RE.search(buf)
                if m:
                    pct = int(m.group(1))
                    now = time.monotonic()
                    if pct != last_pct and now - last_emit >= _PROGRESS_MIN_INTERVAL:
                        self.progress.emit(min(pct, 99))
                        last_pct = pct
                        last_emit = now
        finally:
            proc.wait()

        if proc.returncode != 0:
            err = (proc.stderr.read().decode(errors="ignore") if proc.stderr else "").strip()
            raise RuntimeError(f"UnRAR failed: {err or f'exit {proc.returncode}'}")
