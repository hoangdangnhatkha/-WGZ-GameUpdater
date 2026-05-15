from __future__ import annotations

import logging

from PyQt6.QtCore import QPoint, Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QLinearGradient, QPainter, QPen
from PyQt6.QtWidgets import (
    QApplication, QFrame, QHBoxLayout, QLabel,
    QPushButton, QVBoxLayout, QWidget,
)

from .google_auth import GoogleAuthWorker
from .session import AuthSession

log = logging.getLogger(__name__)

_PANEL_W = 560   # left panel width


class LoginWindow(QWidget):
    """Full-screen pre-auth gate — shown before MainWindow."""

    authenticated = pyqtSignal(object, object)  # UserProfile, Credentials

    def __init__(self) -> None:
        super().__init__()
        self.setFixedSize(1280, 800)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | Qt.WindowType.Window
        )
        self.setObjectName("LoginRoot")
        self._drag_pos: QPoint | None = None
        self._worker: GoogleAuthWorker | None = None
        self._blink_on = True

        # Cursor blink timer
        self._blink = QTimer(self)
        self._blink.setInterval(550)
        self._blink.timeout.connect(self._tick_blink)
        self._blink.start()

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        outer.addWidget(self._build_title_bar())

        body = QHBoxLayout()
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(0)
        body.addWidget(self._build_left_panel())
        body.addWidget(self._build_right_panel(), 1)
        outer.addLayout(body, 1)

    # ── Panel builders ────────────────────────────────────────────

    def _build_title_bar(self) -> QWidget:
        bar = QWidget(self)
        bar.setObjectName("LoginTitleBar")
        bar.setFixedHeight(40)
        bar.mousePressEvent = self._tb_press
        bar.mouseMoveEvent = self._tb_move

        row = QHBoxLayout(bar)
        row.setContentsMargins(20, 0, 0, 0)
        row.setSpacing(0)

        lbl = QLabel("WGZ  //  GAME UPDATER", bar)
        lbl.setObjectName("LoginTitleLabel")
        row.addWidget(lbl)
        row.addStretch(1)

        close = QPushButton("×", bar)
        close.setObjectName("TitleBarClose")
        close.setFixedSize(46, 40)
        close.clicked.connect(self.close)
        row.addWidget(close)
        return bar

    def _build_left_panel(self) -> QWidget:
        panel = QWidget(self)
        panel.setObjectName("LoginLeftPanel")
        panel.setFixedWidth(_PANEL_W)

        v = QVBoxLayout(panel)
        v.setContentsMargins(60, 56, 52, 48)
        v.setSpacing(0)

        logo = QLabel("WGZ", panel)
        logo.setObjectName("LoginLogo")
        v.addWidget(logo)

        sub = QLabel("GAME UPDATER", panel)
        sub.setObjectName("LoginLogoSub")
        v.addWidget(sub)

        v.addSpacing(28)
        v.addWidget(self._hrule(panel))
        v.addSpacing(30)

        hdr = QLabel("// FEATURES", panel)
        hdr.setObjectName("LoginFeatureHeader")
        v.addWidget(hdr)
        v.addSpacing(18)

        for feat in [
            "▸   TẢI GAME & MOD TỰ ĐỘNG",
            "▸   QUẢN LÝ TÀI KHOẢN GAME",
            "▸   XEM HƯỚNG DẪN CÀI ĐẶT",
            "▸   TẢI TRỰC TIẾP TỪ GOOGLE DRIVE",
            "▸   CẬP NHẬT VÀ VÁ LỖI TỰ ĐỘNG",
        ]:
            lbl = QLabel(feat, panel)
            lbl.setObjectName("LoginFeatureItem")
            v.addWidget(lbl)
            v.addSpacing(10)

        v.addStretch(1)

        note = QLabel("// GOOGLE OAUTH 2.0  ·  TLS ENCRYPTED", panel)
        note.setObjectName("LoginFooterNote")
        v.addWidget(note)

        return panel

    def _build_right_panel(self) -> QWidget:
        panel = QWidget(self)
        panel.setObjectName("LoginRightPanel")

        v = QVBoxLayout(panel)
        v.setContentsMargins(72, 0, 72, 72)
        v.setSpacing(0)
        v.addStretch(2)

        section = QLabel("// CLEARANCE REQUIRED", panel)
        section.setObjectName("LoginSectionHeader")
        v.addWidget(section)

        v.addSpacing(14)

        heading = QLabel("IDENTITY\nVERIFICATION", panel)
        heading.setObjectName("LoginHeading")
        v.addWidget(heading)

        v.addSpacing(22)

        desc = QLabel(
            "HỆ THỐNG NÀY SỬ DỤNG XÁC THỰC GOOGLE.\n"
            "TÀI KHOẢN CỦA BẠN XÁC ĐỊNH QUYỀN TRUY CẬP TẢI XUỐNG.",
            panel,
        )
        desc.setObjectName("LoginDesc")
        desc.setWordWrap(True)
        v.addWidget(desc)

        v.addSpacing(44)

        self._auth_btn = QPushButton("  G   ĐĂNG NHẬP VỚI GOOGLE  →", panel)
        self._auth_btn.setObjectName("GoogleSignInButton")
        self._auth_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._auth_btn.setFixedHeight(52)
        self._auth_btn.clicked.connect(self._on_sign_in)
        v.addWidget(self._auth_btn)

        v.addSpacing(24)

        # Status row: text + blinking cursor
        status_row = QHBoxLayout()
        status_row.setSpacing(6)
        self._status_lbl = QLabel("STATUS :  AWAITING AUTHENTICATION", panel)
        self._status_lbl.setObjectName("LoginStatus")
        status_row.addWidget(self._status_lbl)
        self._cursor_lbl = QLabel("█", panel)
        self._cursor_lbl.setObjectName("LoginCursor")
        status_row.addWidget(self._cursor_lbl)
        status_row.addStretch(1)
        v.addLayout(status_row)

        v.addSpacing(14)

        self._error_lbl = QLabel("", panel)
        self._error_lbl.setObjectName("LoginError")
        self._error_lbl.setWordWrap(True)
        self._error_lbl.hide()
        v.addWidget(self._error_lbl)

        v.addStretch(3)
        return panel

    # ── Helpers ───────────────────────────────────────────────────

    @staticmethod
    def _hrule(parent) -> QFrame:
        r = QFrame(parent)
        r.setFrameShape(QFrame.Shape.HLine)
        r.setObjectName("LoginRule")
        r.setFixedHeight(1)
        return r

    # ── Paint ─────────────────────────────────────────────────────

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        rect = self.rect()

        # Base fill
        painter.fillRect(rect, QColor("#07070a"))

        # Left panel background
        painter.fillRect(0, 0, _PANEL_W, rect.height(), QColor("#0a0a0e"))

        # Vertical divider
        painter.fillRect(_PANEL_W, 40, 1, rect.height() - 40, QColor("#24242f"))

        # Scan lines (full width, below title bar)
        pen = QPen(QColor(15, 15, 21, 38), 1)
        painter.setPen(pen)
        for y in range(40, rect.height(), 3):
            painter.drawLine(0, y, rect.width(), y)

        # Lime top accent bar
        painter.fillRect(0, 0, rect.width(), 2, QColor("#d8ff3a"))

        # Title-bar bottom separator
        painter.fillRect(0, 40, rect.width(), 1, QColor("#24242f"))

        # Corner bracket — top-left (inside left panel)
        painter.setPen(QPen(QColor("#d8ff3a"), 1))
        painter.drawLine(22, 46, 22, 76)
        painter.drawLine(22, 46, 52, 46)

        # Corner bracket — bottom-right (inside right panel)
        r = rect
        painter.drawLine(r.right() - 22, r.bottom() - 44, r.right() - 22, r.bottom() - 2)
        painter.drawLine(r.right() - 52, r.bottom() - 2, r.right() - 22, r.bottom() - 2)

        # Subtle diagonal texture in left panel (very faint)
        painter.setPen(QPen(QColor(216, 255, 58, 8), 1))
        for i in range(-800, 600, 44):
            painter.drawLine(i, 40, i + rect.height(), rect.height())

        painter.end()

    # ── Drag ──────────────────────────────────────────────────────

    def _tb_press(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def _tb_move(self, event) -> None:
        if event.buttons() == Qt.MouseButton.LeftButton and self._drag_pos is not None:
            self.move(event.globalPosition().toPoint() - self._drag_pos)

    # ── Auth flow ─────────────────────────────────────────────────

    def _on_sign_in(self) -> None:
        self._auth_btn.setEnabled(False)
        self._auth_btn.setText("  ⟳   ĐANG XỬ LÝ...")
        self._error_lbl.hide()
        self._set_status("Đang khởi động luồng xác thực...")

        self._worker = GoogleAuthWorker(self)
        self._worker.status_update.connect(self._set_status)
        self._worker.authenticated.connect(self._on_auth_ok)
        self._worker.failed.connect(self._on_auth_fail)
        self._worker.start()

    def _set_status(self, msg: str) -> None:
        self._status_lbl.setText(f"STATUS :  {msg.upper()}")

    def _on_auth_ok(self, profile, credentials) -> None:
        self._set_status("XÁC THỰC THÀNH CÔNG")
        self._blink.stop()
        self._cursor_lbl.setText("■")
        self._cursor_lbl.setStyleSheet("color:#d8ff3a;")
        self.authenticated.emit(profile, credentials)
        QTimer.singleShot(600, self.close)

    def _on_auth_fail(self, error: str) -> None:
        self._auth_btn.setEnabled(True)
        self._auth_btn.setText("  G   ĐĂNG NHẬP VỚI GOOGLE  →")
        self._set_status("XÁC THỰC THẤT BẠI — THỬ LẠI")
        self._error_lbl.setText(f"✗  {error}")
        self._error_lbl.show()

    def _tick_blink(self) -> None:
        self._blink_on = not self._blink_on
        self._cursor_lbl.setVisible(self._blink_on)

    # ── Lifecycle ─────────────────────────────────────────────────

    def closeEvent(self, event) -> None:
        if self._worker and self._worker.isRunning():
            self._worker.quit()
        if not AuthSession.is_authenticated():
            QApplication.quit()
        event.accept()
