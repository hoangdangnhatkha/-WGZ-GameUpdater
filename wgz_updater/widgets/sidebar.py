from __future__ import annotations

from dataclasses import dataclass

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QButtonGroup,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


@dataclass(frozen=True)
class NavItem:
    key: str
    label: str
    icon_glyph: str = ""


class _UserBadge(QWidget):
    """Compact user identity panel at the bottom of the sidebar."""

    logout_requested = pyqtSignal()

    def __init__(self, profile, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("UserBadge")

        row = QHBoxLayout(self)
        row.setContentsMargins(14, 10, 14, 10)
        row.setSpacing(10)

        # Avatar circle (initials)
        avatar = QLabel(profile.initials, self)
        avatar.setObjectName("UserAvatar")
        avatar.setFixedSize(34, 34)
        avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        row.addWidget(avatar)

        # Name + email
        info = QVBoxLayout()
        info.setSpacing(1)
        name_lbl = QLabel(profile.display_name, self)
        name_lbl.setObjectName("UserName")
        info.addWidget(name_lbl)

        email_lbl = QLabel(profile.email, self)
        email_lbl.setObjectName("UserEmail")
        info.addWidget(email_lbl)
        row.addLayout(info, 1)

        # Logout button
        logout = QPushButton("↩", self)
        logout.setObjectName("LogoutButton")
        logout.setFixedSize(28, 28)
        logout.setToolTip("Đăng xuất")
        logout.setCursor(Qt.CursorShape.PointingHandCursor)
        logout.clicked.connect(self.logout_requested)
        row.addWidget(logout)


class Sidebar(QFrame):
    nav_changed = pyqtSignal(str)
    logout_requested = pyqtSignal()

    def __init__(
        self,
        items: list[NavItem],
        parent: QWidget | None = None,
        user_profile=None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("Sidebar")
        self.setFixedWidth(232)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 6, 0, 0)
        layout.setSpacing(0)

        brand = QLabel("WGZ", self)
        brand.setObjectName("SidebarBrand")
        layout.addWidget(brand)

        tagline = QLabel("// GAME UPDATER · ONLINE", self)
        tagline.setObjectName("SidebarTagline")
        layout.addWidget(tagline)

        section = QLabel("NAVIGATE", self)
        section.setObjectName("SidebarSection")
        layout.addWidget(section)

        self._group = QButtonGroup(self)
        self._group.setExclusive(True)
        self._buttons: dict[str, QPushButton] = {}

        for i, item in enumerate(items, start=1):
            label = f"  {i:02d}    {item.label.upper()}"
            btn = QPushButton(label, self)
            btn.setObjectName("NavItem")
            btn.setCheckable(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setFocusPolicy(Qt.FocusPolicy.TabFocus)
            btn.clicked.connect(lambda _checked, k=item.key: self._on_clicked(k))
            self._group.addButton(btn)
            self._buttons[item.key] = btn
            layout.addWidget(btn)

        layout.addStretch(1)

        # ── User panel ──────────────────────────────────────────
        sep = QFrame(self)
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setObjectName("SidebarUserSep")
        sep.setFixedHeight(1)
        layout.addWidget(sep)

        if user_profile is not None:
            badge = _UserBadge(user_profile, self)
            badge.logout_requested.connect(self._on_logout)
            layout.addWidget(badge)
        else:
            footer = QLabel("v.0.0.1  ·  PyQt6", self)
            footer.setObjectName("SidebarSection")
            layout.addWidget(footer)

        if items:
            self._buttons[items[0].key].setChecked(True)

    def _on_clicked(self, key: str) -> None:
        self.nav_changed.emit(key)

    def _on_logout(self) -> None:
        from ..features.auth.google_auth import clear_credentials
        from ..features.auth.session import AuthSession
        clear_credentials()
        AuthSession.clear()
        self.logout_requested.emit()

    def select(self, key: str) -> None:
        btn = self._buttons.get(key)
        if btn:
            btn.setChecked(True)
            self.nav_changed.emit(key)
