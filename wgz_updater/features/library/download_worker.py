from __future__ import annotations

import io
import logging
import os
import re
import sys
import tempfile
from pathlib import Path

from PyQt6.QtCore import QThread, pyqtSignal

log = logging.getLogger(__name__)

_PERCENT_RE = re.compile(r"(\d{1,3})\s*%")
_SPEED_RE = re.compile(r"([\d\.]+)\s?([KMG]?B/s)")


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
    progress = pyqtSignal(int)        # 0..100
    speed = pyqtSignal(str)           # "12.3 MB/s"
    status = pyqtSignal(str)          # human-readable
    finished_ok = pyqtSignal(str)     # final path
    failed = pyqtSignal(str)          # error message

    def __init__(self, url: str, dest_dir: Path, file_hint: str = "download.bin", parent=None) -> None:
        super().__init__(parent)
        self._url = url
        self._dest_dir = Path(dest_dir)
        self._file_hint = file_hint
        self._cancel = False

    def cancel(self) -> None:
        self._cancel = True

    def run(self) -> None:
        try:
            import gdown
        except Exception as exc:
            self.failed.emit(f"gdown not available: {exc}")
            return

        self._dest_dir.mkdir(parents=True, exist_ok=True)
        out_path = self._dest_dir / self._file_hint

        original_stderr = sys.stderr
        trap = _GdownProgressTrap(
            on_percent=lambda p: self.progress.emit(p),
            on_speed=lambda s: self.speed.emit(s),
        )
        sys.stderr = trap
        try:
            self.status.emit("Đang kết nối Google Drive...")
            result = gdown.download(self._url, str(out_path), quiet=False, fuzzy=True, resume=True)
            if self._cancel:
                self.failed.emit("Đã hủy")
                return
            if not result or not Path(result).exists():
                self.failed.emit("Tải thất bại")
                return
            self.progress.emit(100)
            self.finished_ok.emit(str(result))
        except Exception as exc:
            log.exception("Download failed")
            self.failed.emit(str(exc))
        finally:
            sys.stderr = original_stderr
