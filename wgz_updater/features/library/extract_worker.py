from __future__ import annotations

import logging
import shutil
import subprocess
import zipfile
from pathlib import Path

from PyQt6.QtCore import QThread, pyqtSignal

from ...core.paths import PACKAGE_ROOT, UNRAR_EXE

log = logging.getLogger(__name__)


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
        with zipfile.ZipFile(self._archive, "r") as zf:
            members = zf.infolist()
            total = max(len(members), 1)
            for i, m in enumerate(members, 1):
                pwd_bytes = self._password.encode("utf-8") if self._password else None
                zf.extract(m, str(self._target), pwd=pwd_bytes)
                self.progress.emit(int(i * 100 / total))

    def _extract_rar(self) -> None:
        unrar = _resolve_unrar()
        if not unrar:
            raise RuntimeError("UnRAR.exe not found")
        self.status.emit("Đang giải nén RAR...")
        cmd = [str(unrar), "x", "-y", "-o+"]
        if self._password:
            cmd.append(f"-p{self._password}")
        cmd.extend([str(self._archive), str(self._target) + "\\"])
        proc = subprocess.run(cmd, capture_output=True, text=True)
        if proc.returncode != 0:
            raise RuntimeError(f"UnRAR failed: {proc.stderr.strip() or proc.stdout.strip()}")
