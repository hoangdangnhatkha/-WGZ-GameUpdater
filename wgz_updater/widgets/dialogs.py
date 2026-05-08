from __future__ import annotations

import shutil

from PyQt6.QtWidgets import QDialog, QDialogButtonBox, QLabel, QMessageBox, QVBoxLayout, QWidget

from ..core.config import Game


def wgz_info(parent: QWidget | None, title: str, message: str) -> None:
    """Show an information dialog."""
    mb = QMessageBox(parent)
    mb.setWindowTitle(title)
    mb.setText(message)
    mb.setIcon(QMessageBox.Icon.Information)
    mb.exec()


def wgz_warn(parent: QWidget | None, title: str, message: str) -> None:
    """Show a warning dialog."""
    mb = QMessageBox(parent)
    mb.setWindowTitle(title)
    mb.setText(message)
    mb.setIcon(QMessageBox.Icon.Warning)
    mb.exec()


def wgz_error(parent: QWidget | None, title: str, message: str) -> None:
    """Show an error dialog."""
    mb = QMessageBox(parent)
    mb.setWindowTitle(title)
    mb.setText(message)
    mb.setIcon(QMessageBox.Icon.Critical)
    mb.exec()


def wgz_ask(parent: QWidget | None, title: str, message: str) -> bool:
    """Ask a yes/no question. Returns True if user clicked Yes."""
    result = QMessageBox.question(
        parent,
        title,
        message,
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
    )
    return result == QMessageBox.StandardButton.Yes


class DownloadConfirmDialog(QDialog):
    """Shows file count, disk usage estimate, and asks user to confirm before download."""

    def __init__(
        self,
        parent: QWidget | None,
        game: "Game",
        url_count: int,
        install_path: str = "",
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Xác nhận tải về")
        self.setMinimumWidth(360)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # Free disk space
        free_gb = 0.0
        if install_path:
            try:
                usage = shutil.disk_usage(install_path)
                free_gb = usage.free / (1024 ** 3)
            except Exception:
                pass

        parts_text = f"{url_count} phần" if url_count > 1 else "1 phần"
        msg = (
            f"Tải <b>{game.name}</b> ({parts_text})?\n\n"
            f"Dung lượng trống: {free_gb:.1f} GB"
        )
        lbl = QLabel(msg, self)
        lbl.setWordWrap(True)
        layout.addWidget(lbl)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel,
            self,
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    @classmethod
    def ask(
        cls,
        parent: QWidget | None,
        game: "Game",
        url_count: int,
        install_path: str = "",
    ) -> bool:
        """Convenience: show dialog and return True if user confirmed."""
        dlg = cls(parent, game, url_count, install_path)
        return dlg.exec() == QDialog.DialogCode.Accepted
