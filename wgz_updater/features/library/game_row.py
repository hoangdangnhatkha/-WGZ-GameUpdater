from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout

from ...core.config import Game
from ...resources.strings_vi import ACTION_DOWNLOAD, ACTION_UPDATE
from .image_loader import ImageLoader
from .models import InstallRegistry, InstallStatus

_TAG_COLORS: dict[str, str] = {
    "HOT":  "#ff5b3c",
    "GOTY": "#ffd700",
    "NEW":  "#4dffaa",
    "UPD":  "#4f7cff",
    "BEST": "#b48bff",
    "FIX":  "#ffc04d",
}


class GameRow(QFrame):
    """High-density horizontal manifest row.

    Layout:  [thumb 140×72] [idx ##] [title + tag/version meta] [status pill] [action btn]
    """

    clicked = pyqtSignal(object)  # list[Game]

    def __init__(
        self,
        entries: list[Game],
        registry: InstallRegistry,
        image_url: str = "",
        index: int = 0,
        parent=None,
    ) -> None:
        super().__init__(parent)
        if not entries:
            raise ValueError("GameRow requires at least one Game entry")
        self._entries = entries
        self._game = entries[0]
        self._registry = registry
        self._display_name = (self._game.game or self._game.name or "").strip()
        self.setObjectName("GameRow")
        self.setFixedHeight(82)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 16, 0)
        layout.setSpacing(0)

        # Thumbnail
        self._thumb = QLabel(self)
        self._thumb.setFixedSize(140, 80)
        self._thumb.setObjectName("RowThumb")
        self._thumb.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._thumb)

        # Index column
        idx_lbl = QLabel(f"{index:02d}", self)
        idx_lbl.setObjectName("RowIndex")
        idx_lbl.setFixedWidth(58)
        idx_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(idx_lbl)

        # Title block
        info = QVBoxLayout()
        info.setSpacing(2)
        info.setContentsMargins(2, 14, 12, 14)

        title = QLabel(self._display_name, self)
        title.setObjectName("RowTitle")
        info.addWidget(title)

        meta_row = QHBoxLayout()
        meta_row.setSpacing(12)
        meta_row.setContentsMargins(0, 0, 0, 0)

        # Tag
        tag_text = ""
        for e in entries:
            if e.tag and e.tag.upper() in _TAG_COLORS:
                tag_text = e.tag.upper()
                break
        if tag_text:
            color = _TAG_COLORS[tag_text]
            tag_lbl = QLabel(f"[ {tag_text} ]", self)
            tag_lbl.setStyleSheet(
                f"font-family:'Cascadia Mono',Consolas,monospace;"
                f"color:{color};font-size:10px;font-weight:700;letter-spacing:1.2px;"
            )
            meta_row.addWidget(tag_lbl)

        # Variant count
        if len(entries) > 1:
            count = QLabel(f"{len(entries):02d} BẢN", self)
            count.setObjectName("RowMeta")
            meta_row.addWidget(count)

        # Version
        version = ""
        for e in entries:
            if e.version:
                version = e.version
                break
        if version:
            ver_lbl = QLabel(f"v{version.lstrip('v')}", self)
            ver_lbl.setObjectName("RowMeta")
            meta_row.addWidget(ver_lbl)

        # Type indicator (zip/rar count)
        types = sorted({(e.type or "zip").upper() for e in entries})
        if types:
            type_lbl = QLabel(" / ".join(types), self)
            type_lbl.setObjectName("RowMeta")
            meta_row.addWidget(type_lbl)

        meta_row.addStretch(1)
        info.addLayout(meta_row)

        layout.addLayout(info, 1)

        # Status indicator (right-aligned)
        self._status_lbl = QLabel(self)
        self._status_lbl.setFixedWidth(140)
        self._status_lbl.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )
        layout.addWidget(self._status_lbl)

        # Action button
        self._btn = QPushButton(self)
        self._btn.setFixedSize(120, 34)
        self._btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn.clicked.connect(lambda: self.clicked.emit(self._entries))
        layout.addWidget(self._btn)

        self._refresh_status()

        if image_url:
            ImageLoader.instance().request(image_url, self._set_thumb)

    # ── helpers ───────────────────────────────────────────────────

    def _set_thumb(self, pixmap: QPixmap) -> None:
        scaled = pixmap.scaled(
            140, 80,
            Qt.AspectRatioMode.KeepAspectRatioByExpanding,
            Qt.TransformationMode.SmoothTransformation,
        )
        self._thumb.setPixmap(scaled)

    def _refresh_status(self) -> None:
        statuses = [self._registry.status_for(g) for g in self._entries]
        if any(s == InstallStatus.INSTALLED for s in statuses):
            self._status_lbl.setText("● INSTALLED")
            self._status_lbl.setStyleSheet(
                "font-family:'Cascadia Mono',Consolas,monospace;"
                "color:#4dffaa;font-size:10px;font-weight:700;letter-spacing:1.2px;"
            )
            self._btn.setText("CHI TIẾT")
            self._btn.setObjectName("")
        elif any(s == InstallStatus.UPDATE for s in statuses):
            self._status_lbl.setText("▲ UPDATE")
            self._status_lbl.setStyleSheet(
                "font-family:'Cascadia Mono',Consolas,monospace;"
                "color:#ffc04d;font-size:10px;font-weight:700;letter-spacing:1.2px;"
            )
            self._btn.setText(ACTION_UPDATE.upper())
            self._btn.setObjectName("Accent")
        else:
            self._status_lbl.setText("○ NOT INSTALLED")
            self._status_lbl.setStyleSheet(
                "font-family:'Cascadia Mono',Consolas,monospace;"
                "color:#5e5e62;font-size:10px;font-weight:700;letter-spacing:1.2px;"
            )
            self._btn.setText(ACTION_DOWNLOAD.upper())
            self._btn.setObjectName("Accent")
        self._btn.style().unpolish(self._btn)
        self._btn.style().polish(self._btn)

    def refresh(self) -> None:
        self._refresh_status()

    def matches(self, q: str) -> bool:
        if not q:
            return True
        ql = q.lower()
        if ql in self._display_name.lower():
            return True
        return any(
            ql in (e.name or "").lower() or ql in (e.game or "").lower()
            for e in self._entries
        )

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self._entries)
        super().mousePressEvent(event)
