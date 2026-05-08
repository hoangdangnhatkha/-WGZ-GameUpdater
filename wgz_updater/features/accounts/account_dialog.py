from __future__ import annotations

from PyQt6.QtWidgets import (
    QComboBox, QDialog, QDialogButtonBox, QFormLayout,
    QHBoxLayout, QLineEdit, QPushButton, QVBoxLayout, QWidget,
)

from ...resources.strings_vi import (
    LABEL_GAME_TAG, LABEL_NICKNAME, LABEL_SERVICE,
)
from .models import AccountRecord

_KNOWN_SERVICES = ["Steam", "Riot"]


class AccountDialog(QDialog):
    """Add or edit an AccountRecord."""

    def __init__(
        self,
        parent: QWidget | None = None,
        record: AccountRecord | None = None,
        game_names: list[str] | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Thêm tài khoản" if record is None else "Sửa tài khoản")
        self.setMinimumWidth(360)

        layout = QVBoxLayout(self)
        form = QFormLayout()
        layout.addLayout(form)

        self._service = QComboBox(self)
        self._service.addItems(_KNOWN_SERVICES)
        self._service.setEditable(True)
        form.addRow(LABEL_SERVICE, self._service)

        self._nickname = QLineEdit(self)
        form.addRow(LABEL_NICKNAME, self._nickname)

        self._username = QLineEdit(self)
        form.addRow("Username:", self._username)

        # Password with show/hide toggle
        pw_row = QHBoxLayout()
        self._password = QLineEdit(self)
        self._password.setEchoMode(QLineEdit.EchoMode.Password)
        pw_row.addWidget(self._password)
        toggle = QPushButton("👁", self)
        toggle.setFixedWidth(32)
        toggle.setCheckable(True)
        toggle.toggled.connect(
            lambda checked: self._password.setEchoMode(
                QLineEdit.EchoMode.Normal if checked else QLineEdit.EchoMode.Password
            )
        )
        pw_row.addWidget(toggle)
        form.addRow("Mật khẩu:", pw_row)

        self._game = QComboBox(self)
        self._game.addItem("")
        if game_names:
            self._game.addItems(game_names)
        self._game.setEditable(True)
        form.addRow(LABEL_GAME_TAG, self._game)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel,
            parent=self,
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        if record:
            self._service.setCurrentText(record.service)
            self._nickname.setText(record.nickname)
            self._username.setText(record.username)
            self._password.setText(record.password)
            self._game.setCurrentText(record.game)

    def get_record(self) -> AccountRecord:
        return AccountRecord(
            service=self._service.currentText().strip(),
            username=self._username.text().strip(),
            password=self._password.text(),
            nickname=self._nickname.text().strip(),
            game=self._game.currentText().strip(),
        )
