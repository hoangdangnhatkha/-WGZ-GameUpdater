from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QLabel

from ..features.library.models import InstallStatus
from ..resources.strings_vi import STATUS_INSTALLED, STATUS_NOT_INSTALLED, STATUS_UPDATE

_OBJECT_NAMES = {
    InstallStatus.INSTALLED: "PillInstalled",
    InstallStatus.UPDATE: "PillUpdate",
    InstallStatus.NOT_INSTALLED: "PillNotInstalled",
}

_LABELS = {
    InstallStatus.INSTALLED: STATUS_INSTALLED,
    InstallStatus.UPDATE: STATUS_UPDATE,
    InstallStatus.NOT_INSTALLED: STATUS_NOT_INSTALLED,
}


class PillLabel(QLabel):
    def __init__(self, status: InstallStatus = InstallStatus.NOT_INSTALLED, parent=None) -> None:
        super().__init__(parent)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.set_status(status)

    def set_status(self, status: InstallStatus) -> None:
        self.setObjectName(_OBJECT_NAMES[status])
        self.setText(_LABELS[status])
        self.style().unpolish(self)
        self.style().polish(self)
