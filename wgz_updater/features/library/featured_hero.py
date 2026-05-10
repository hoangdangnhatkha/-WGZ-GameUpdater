from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QLinearGradient, QPainter, QPen, QPixmap
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


class FeaturedHero(QFrame):
    """Wide editorial hero card with full-bleed game art and gradient overlay."""

    clicked = pyqtSignal(object)  # list[Game]

    def __init__(self, registry: InstallRegistry, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("FeaturedHero")
        self.setFixedHeight(220)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._registry = registry
        self._entries: list[Game] = []
        self._pixmap: QPixmap | None = None
        self._hover = False

        layout = QHBoxLayout(self)
        layout.setContentsMargins(36, 26, 36, 26)
        layout.setSpacing(0)

        text_col = QVBoxLayout()
        text_col.setSpacing(6)

        # FEATURED ribbon
        ribbon = QLabel("◢ FEATURED · NỔI BẬT", self)
        ribbon.setObjectName("HeroRibbon")
        text_col.addWidget(ribbon)

        # Tag (bracketed)
        self._tag = QLabel("", self)
        self._tag.setObjectName("HeroTag")
        text_col.addWidget(self._tag)

        # Big title
        self._title = QLabel("", self)
        self._title.setObjectName("HeroTitle")
        self._title.setWordWrap(True)
        text_col.addWidget(self._title)

        # Mono meta
        self._meta = QLabel("", self)
        self._meta.setObjectName("HeroMeta")
        text_col.addWidget(self._meta)

        text_col.addStretch(1)

        # CTA row
        cta_row = QHBoxLayout()
        cta_row.setSpacing(8)
        self._cta = QPushButton("XEM CHI TIẾT  →", self)
        self._cta.setObjectName("Accent")
        self._cta.setCursor(Qt.CursorShape.PointingHandCursor)
        self._cta.clicked.connect(lambda: self.clicked.emit(self._entries))
        cta_row.addWidget(self._cta)

        self._sec_btn = QPushButton("", self)
        self._sec_btn.setObjectName("HeroSecondary")
        self._sec_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._sec_btn.clicked.connect(lambda: self.clicked.emit(self._entries))
        cta_row.addWidget(self._sec_btn)

        cta_row.addStretch(1)
        text_col.addLayout(cta_row)

        layout.addLayout(text_col, 5)
        layout.addStretch(4)  # space the gradient flows over

    # ── public ────────────────────────────────────────────────────

    def set_game(
        self,
        entries: list[Game],
        canonical_name: str,
        image_url: str = "",
    ) -> None:
        self._entries = entries
        self._title.setText(canonical_name.upper())

        tag_text = ""
        for e in entries:
            if e.tag and e.tag.upper() in _TAG_COLORS:
                tag_text = e.tag.upper()
                break
        if tag_text:
            color = _TAG_COLORS[tag_text]
            self._tag.setText(f"[ {tag_text} ]")
            self._tag.setStyleSheet(
                f"font-family:'Cascadia Mono',Consolas,monospace;"
                f"color:{color};font-size:11px;font-weight:700;letter-spacing:1.5px;"
            )
            self._tag.show()
        else:
            self._tag.hide()

        # Status + meta
        statuses = [self._registry.status_for(g) for g in entries]
        if any(s == InstallStatus.INSTALLED for s in statuses):
            status_word = "INSTALLED"
            sec_word = "MỞ"
        elif any(s == InstallStatus.UPDATE for s in statuses):
            status_word = "UPDATE AVAILABLE"
            sec_word = ACTION_UPDATE.upper()
        else:
            status_word = "READY TO DEPLOY"
            sec_word = ACTION_DOWNLOAD.upper()
        version = ""
        for e in entries:
            if e.version:
                version = e.version
                break
        meta_parts = [f"{len(entries):02d} BẢN"]
        if version:
            meta_parts.append(f"v{version.lstrip('v')}")
        meta_parts.append(status_word)
        self._meta.setText("   ·   ".join(meta_parts))
        self._sec_btn.setText(sec_word)

        # Image
        self._pixmap = None
        self.update()
        if image_url:
            ImageLoader.instance().request(image_url, self._set_image)

    # ── paint ─────────────────────────────────────────────────────

    def _set_image(self, pixmap: QPixmap) -> None:
        self._pixmap = pixmap
        self.update()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.rect()

        # Base
        painter.fillRect(rect, QColor("#0a0a0e"))

        # Image (right-anchored, height-fills)
        if self._pixmap and not self._pixmap.isNull():
            scaled = self._pixmap.scaledToHeight(
                rect.height(),
                Qt.TransformationMode.SmoothTransformation,
            )
            img_rect = scaled.rect()
            img_rect.moveRight(rect.right())
            img_rect.moveTop(0)
            painter.drawPixmap(img_rect, scaled)

            # Multi-stop gradient: opaque-dark left, transparent right
            gradient = QLinearGradient(0, 0, rect.width(), 0)
            gradient.setColorAt(0.0, QColor(10, 10, 14, 255))
            gradient.setColorAt(0.45, QColor(10, 10, 14, 235))
            gradient.setColorAt(0.7, QColor(10, 10, 14, 140))
            gradient.setColorAt(1.0, QColor(10, 10, 14, 0))
            painter.fillRect(rect, gradient)

            # Vertical bottom-fade (atmosphere)
            v_grad = QLinearGradient(0, rect.bottom() - 60, 0, rect.bottom())
            v_grad.setColorAt(0.0, QColor(10, 10, 14, 0))
            v_grad.setColorAt(1.0, QColor(10, 10, 14, 180))
            painter.fillRect(rect, v_grad)

        # Border (lime on hover, rule otherwise)
        border_color = QColor("#d8ff3a") if self._hover else QColor("#24242f")
        pen = QPen(border_color, 1)
        painter.setPen(pen)
        painter.drawRect(rect.adjusted(0, 0, -1, -1))

        # Corner mark (top-right)
        painter.setPen(QPen(QColor("#d8ff3a"), 2))
        painter.drawLine(rect.right() - 22, rect.top() + 2, rect.right() - 2, rect.top() + 2)
        painter.drawLine(rect.right() - 2, rect.top() + 2, rect.right() - 2, rect.top() + 22)

        # Bottom-left bracket
        painter.drawLine(rect.left() + 2, rect.bottom() - 22, rect.left() + 2, rect.bottom() - 2)
        painter.drawLine(rect.left() + 2, rect.bottom() - 2, rect.left() + 22, rect.bottom() - 2)

        painter.end()

    # ── interactions ─────────────────────────────────────────────

    def enterEvent(self, event) -> None:
        self._hover = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:
        self._hover = False
        self.update()
        super().leaveEvent(event)

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton and self._entries:
            self.clicked.emit(self._entries)
        super().mousePressEvent(event)
