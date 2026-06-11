"""Application-modal loading dialog with a custom animated busy bar.

Plain `QProgressBar` with `range(0,0)` loses its indeterminate animation as
soon as a QSS rule targets `::chunk` — Qt's stylesheet style engine takes over
rendering and the chunk is painted statically, making the dialog look frozen.
This module ships a `_BusyBar` widget driven by `QPropertyAnimation` so the
animation works regardless of stylesheet rules.
"""

from __future__ import annotations

from typing import Callable, Mapping, Optional

from PyQt6.QtCore import (
    QEasingCurve,
    QPropertyAnimation,
    QRectF,
    Qt,
    QThread,
    pyqtProperty,
)
from PyQt6.QtGui import QColor, QPainter
from PyQt6.QtWidgets import (
    QApplication,
    QDialog,
    QLabel,
    QVBoxLayout,
    QWidget,
)

_DEFAULT_MESSAGE = "Đang tải dữ liệu..."


class _BusyBar(QWidget):
    """Indeterminate busy bar — animated chunk slides left↔right."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("LoadingDialogBar")
        self.setFixedHeight(6)
        self._pos = 0.0  # 0.0 .. 1.0 (chunk center position along track)
        self._chunk_ratio = 0.35  # chunk width as fraction of track width
        self._track = QColor("#14141a")
        self._chunk = QColor("#6b6bff")

        self._anim = QPropertyAnimation(self, b"pos", self)
        self._anim.setDuration(1100)
        self._anim.setStartValue(0.0)
        self._anim.setEndValue(1.0)
        self._anim.setEasingCurve(QEasingCurve.Type.InOutSine)
        self._anim.setLoopCount(-1)

    def showEvent(self, event):  # noqa: N802 - Qt API
        super().showEvent(event)
        self._anim.start()

    def hideEvent(self, event):  # noqa: N802 - Qt API
        self._anim.stop()
        super().hideEvent(event)

    def _get_pos(self) -> float:
        return self._pos

    def _set_pos(self, value: float) -> None:
        # Triangle wave: 0→1→0 over [0,1] domain so chunk bounces.
        self._pos = value
        self.update()

    pos = pyqtProperty(float, fget=_get_pos, fset=_set_pos)

    def paintEvent(self, event):  # noqa: N802 - Qt API
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = QRectF(self.rect())
        radius = rect.height() / 2.0

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(self._track)
        painter.drawRoundedRect(rect, radius, radius)

        chunk_w = rect.width() * self._chunk_ratio
        travel = rect.width() - chunk_w
        # Bounce: 0..1..0 over animation pos (which goes 0..1 each cycle)
        # Use sine-ish bounce: pos in [0,1] → t = 1 - |2*pos - 1| in [0,1]
        t = 1.0 - abs(2.0 * self._pos - 1.0)
        x = rect.x() + travel * t
        chunk_rect = QRectF(x, rect.y(), chunk_w, rect.height())
        painter.setBrush(self._chunk)
        painter.drawRoundedRect(chunk_rect, radius, radius)
        painter.end()


class LoadingDialog(QDialog):
    def __init__(self, parent: QWidget | None = None, message: str = _DEFAULT_MESSAGE) -> None:
        super().__init__(parent)
        self.setObjectName("LoadingDialog")
        self.setWindowFlags(
            Qt.WindowType.Dialog
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.CustomizeWindowHint
        )
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setFixedSize(280, 120)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, False)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(16)

        self._label = QLabel(message, self)
        self._label.setObjectName("LoadingDialogLabel")
        self._label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._label.setWordWrap(True)
        layout.addWidget(self._label)

        self._bar = _BusyBar(self)
        layout.addWidget(self._bar)

    def set_message(self, text: str) -> None:
        self._label.setText(text)

    def _center_on_parent(self) -> None:
        parent = self.parentWidget()
        if parent is not None:
            top = parent.window()
            if top is not None and top.isVisible():
                geo = top.frameGeometry()
                self.move(
                    geo.center().x() - self.width() // 2,
                    geo.center().y() - self.height() // 2,
                )
                return
        screen = self.screen() or QApplication.primaryScreen()
        if screen is not None:
            geo = screen.availableGeometry()
            self.move(
                geo.center().x() - self.width() // 2,
                geo.center().y() - self.height() // 2,
            )

    def showEvent(self, event):  # noqa: N802 - Qt API
        self._center_on_parent()
        super().showEvent(event)
        self.raise_()
        self.activateWindow()

    def closeEvent(self, event):  # noqa: N802 - Qt API
        if not self.result():
            event.ignore()
        else:
            event.accept()

    def keyPressEvent(self, event):  # noqa: N802 - Qt API
        if event.key() in (Qt.Key.Key_Escape, Qt.Key.Key_Return, Qt.Key.Key_Enter):
            event.ignore()
            return
        super().keyPressEvent(event)


def run_blocking(
    parent: QWidget | None,
    worker: QThread,
    *,
    message: str = _DEFAULT_MESSAGE,
    slots: Optional[Mapping[str, Optional[Callable]]] = None,
) -> LoadingDialog:
    """Show a modal LoadingDialog while `worker` runs.

    `slots` maps worker signal names to optional callbacks. Each signal is wired
    so the dialog closes BEFORE the callback runs — this prevents result toasts
    (QMessageBox) from stacking on top of the still-visible loading dialog.

    The dialog also closes when QThread's own `finished` signal fires, as a
    safety net for workers that don't emit a custom completion signal.
    """
    dlg = LoadingDialog(parent, message)

    def _make(cb: Optional[Callable]) -> Callable:
        def handler(*args):
            if dlg.isVisible():
                dlg.done(QDialog.DialogCode.Accepted)
            if cb is not None:
                cb(*args)
        return handler

    if slots:
        for sig_name, cb in slots.items():
            sig = getattr(worker, sig_name, None)
            if sig is None:
                continue
            sig.connect(_make(cb))

    worker.finished.connect(_make(None))
    worker.start()
    dlg.exec()
    return dlg
