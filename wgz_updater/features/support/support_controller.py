from __future__ import annotations

import json
import logging

from PyQt6.QtCore import QObject, Qt, QThread, pyqtSignal
from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QLabel,
    QLineEdit,
    QMessageBox,
    QVBoxLayout,
    QWidget,
)

from ...core.config import SupportConfig, load_config
from ...core.paths import CONFIG_BUNDLED, CONFIG_FILENAME, CONFIG_LOCAL, PACKAGE_ROOT
from ...resources.strings_vi import (
    DIALOG_CANCEL,
    DIALOG_ERROR_TITLE,
    SUPPORT_CONFIRM_SEND,
    SUPPORT_DIALOG_BODY,
    SUPPORT_DIALOG_TITLE,
    SUPPORT_INSTALL_BODY,
    SUPPORT_INSTALL_CONFIRM,
    SUPPORT_INSTALL_TITLE,
    SUPPORT_NO_CONFIG,
    SUPPORT_NO_RUSTDESK,
    SUPPORT_OTP_EMPTY,
    SUPPORT_OTP_PLACEHOLDER,
    SUPPORT_OTP_PROMPT_BODY,
    SUPPORT_OTP_PROMPT_TITLE,
    SUPPORT_OTP_SEND,
)
from ..auth.session import AuthSession
from . import rustdesk_service
from .discord_notifier import DiscordNotifyError, post_support_request

log = logging.getLogger(__name__)


# ── Support config resolution ────────────────────────────────────────


def _read_support_from(path) -> SupportConfig | None:
    if not path or not path.exists():
        return None
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        log.exception("Failed reading %s for support config", path)
        return None
    blob = raw.get("support") if isinstance(raw, dict) else None
    if not isinstance(blob, dict):
        return None
    try:
        return SupportConfig(**blob)
    except Exception:
        log.exception("Invalid support block in %s", path)
        return None


def _resolve_support_config() -> SupportConfig | None:
    """Resolve support config across cache → bundled → repo-root fallback."""
    try:
        cfg = load_config(prefer_remote=False)
    except Exception:
        cfg = None

    if cfg is not None and (cfg.support.discord_webhook or "").strip():
        return cfg.support

    candidates = (
        CONFIG_LOCAL,
        CONFIG_BUNDLED,
        PACKAGE_ROOT.parent / CONFIG_FILENAME,
    )
    for path in candidates:
        sc = _read_support_from(path)
        if sc and sc.discord_webhook.strip():
            return sc

    return None


# ── Workers ─────────────────────────────────────────────────────────


class _InstallWorker(QThread):
    """Run `--silent-install` via UAC and wait for install completion."""

    succeeded = pyqtSignal()
    cancelled = pyqtSignal()
    failed = pyqtSignal(str)
    timed_out = pyqtSignal()

    def run(self) -> None:
        try:
            rustdesk_service.install_silent_with_uac()
        except rustdesk_service.InstallCancelledError:
            self.cancelled.emit()
            return
        except rustdesk_service.RustDeskError as exc:
            self.failed.emit(str(exc))
            return
        except Exception as exc:
            log.exception("Unexpected install failure")
            self.failed.emit(str(exc))
            return

        if rustdesk_service.wait_for_install():
            self.succeeded.emit()
        else:
            self.timed_out.emit()


class _LaunchWorker(QThread):
    """Launch RustDesk and resolve (id, otp) off the GUI thread."""

    succeeded = pyqtSignal(str, str)  # rustdesk_id, otp ("" when not auto-detected)
    failed = pyqtSignal(str)

    def run(self) -> None:
        try:
            info = rustdesk_service.prepare_session()
        except rustdesk_service.RustDeskError as exc:
            log.warning("RustDesk launch failed: %s", exc)
            self.failed.emit(str(exc))
            return
        except Exception as exc:
            log.exception("Unexpected RustDesk failure")
            self.failed.emit(str(exc))
            return
        self.succeeded.emit(info.rustdesk_id, info.otp or "")


class _NotifyWorker(QThread):
    """POST the support request to Discord off the GUI thread."""

    succeeded = pyqtSignal()
    failed = pyqtSignal(str)

    def __init__(
        self,
        webhook_url: str,
        mention: str,
        rustdesk_id: str,
        password: str,
        user_email: str,
        user_name: str,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._webhook_url = webhook_url
        self._mention = mention
        self._rustdesk_id = rustdesk_id
        self._password = password
        self._user_email = user_email
        self._user_name = user_name

    def run(self) -> None:
        try:
            post_support_request(
                self._webhook_url,
                rustdesk_id=self._rustdesk_id,
                rustdesk_password=self._password,
                user_email=self._user_email,
                user_name=self._user_name,
                mention=self._mention,
            )
        except DiscordNotifyError as exc:
            self.failed.emit(str(exc))
            return
        except Exception as exc:
            log.exception("Unexpected Discord failure")
            self.failed.emit(str(exc))
            return
        self.succeeded.emit()


# ── OTP entry dialog ────────────────────────────────────────────────


class _OtpDialog(QDialog):
    def __init__(self, rustdesk_id: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(SUPPORT_OTP_PROMPT_TITLE)
        self.setModal(True)
        self.setMinimumWidth(440)

        body = QLabel(SUPPORT_OTP_PROMPT_BODY.format(id=rustdesk_id), self)
        body.setWordWrap(True)
        body.setTextFormat(Qt.TextFormat.RichText)

        self._input = QLineEdit(self)
        self._input.setPlaceholderText(SUPPORT_OTP_PLACEHOLDER)
        self._input.setClearButtonEnabled(True)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel,
            parent=self,
        )
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText(SUPPORT_OTP_SEND)
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText(DIALOG_CANCEL)
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addWidget(body)
        layout.addWidget(self._input)
        layout.addWidget(buttons)

    def _on_accept(self) -> None:
        if not self._input.text().strip():
            QMessageBox.warning(self, DIALOG_ERROR_TITLE, SUPPORT_OTP_EMPTY)
            self._input.setFocus()
            return
        self.accept()

    def password(self) -> str:
        return self._input.text().strip()


# ── Controller ──────────────────────────────────────────────────────


class SupportController(QObject):
    def __init__(self, parent_widget: QWidget) -> None:
        super().__init__(parent_widget)
        self._parent = parent_widget
        self._install_worker: _InstallWorker | None = None
        self._launch_worker: _LaunchWorker | None = None
        self._notify_worker: _NotifyWorker | None = None
        self._support_cfg: SupportConfig | None = None
        self._user_email = ""
        self._user_name = ""

    # ── Public entry point ────────────────────────────────────────

    def request_support(self) -> None:
        if self._busy():
            log.info("Support request already in progress — ignoring")
            return

        if not rustdesk_service.is_bundled():
            self._error(SUPPORT_NO_RUSTDESK)
            return

        support_cfg = _resolve_support_config()
        if support_cfg is None or not support_cfg.discord_webhook.strip():
            self._error(SUPPORT_NO_CONFIG)
            return

        if not self._confirm():
            return

        self._support_cfg = support_cfg
        profile = AuthSession.profile()
        self._user_email = getattr(profile, "email", "") if profile else ""
        self._user_name = getattr(profile, "display_name", "") if profile else ""

        needs_install = (
            not rustdesk_service.is_installed()
            or rustdesk_service.read_stored_password() is None
        )
        if needs_install:
            self._prompt_install()
        else:
            self._start_launch()

    def _busy(self) -> bool:
        for w in (self._install_worker, self._launch_worker, self._notify_worker):
            if w is not None and w.isRunning():
                return True
        return False

    # ── Step 0: install gate ─────────────────────────────────────

    def _prompt_install(self) -> None:
        box = QMessageBox(self._parent)
        box.setIcon(QMessageBox.Icon.Question)
        box.setWindowTitle(SUPPORT_INSTALL_TITLE)
        box.setText(SUPPORT_INSTALL_BODY)
        ok = box.addButton(SUPPORT_INSTALL_CONFIRM, QMessageBox.ButtonRole.AcceptRole)
        box.addButton(DIALOG_CANCEL, QMessageBox.ButtonRole.RejectRole)
        box.exec()
        if box.clickedButton() is not ok:
            return

        worker = _InstallWorker(self)
        worker.succeeded.connect(self._on_install_ok)
        worker.cancelled.connect(self._on_install_cancelled)
        worker.failed.connect(self._on_install_failed)
        worker.timed_out.connect(self._on_install_timeout)
        worker.finished.connect(self._cleanup_install_worker)
        self._install_worker = worker
        worker.start()

    def _on_install_ok(self) -> None:
        self._start_launch()

    def _on_install_cancelled(self) -> None:
        log.info("Install cancelled by user")

    def _on_install_failed(self, error: str) -> None:
        log.warning("Install failed: %s", error)

    def _on_install_timeout(self) -> None:
        log.warning("Install timeout")

    # ── Step 1: launch ───────────────────────────────────────────

    def _start_launch(self) -> None:
        worker = _LaunchWorker(self)
        worker.succeeded.connect(self._on_id_ready)
        worker.failed.connect(self._on_launch_failed)
        worker.finished.connect(self._cleanup_launch_worker)
        self._launch_worker = worker
        worker.start()

    # ── Step 1: launch result ─────────────────────────────────────

    def _on_id_ready(self, rustdesk_id: str, otp: str) -> None:
        password = otp.strip()
        if not password:
            dialog = _OtpDialog(rustdesk_id, self._parent)
            if dialog.exec() != QDialog.DialogCode.Accepted:
                return
            password = dialog.password()
        self._send_to_discord(rustdesk_id, password)

    def _on_launch_failed(self, error: str) -> None:
        log.warning("Launch failed: %s", error)

    # ── Step 2: Discord POST ──────────────────────────────────────

    def _send_to_discord(self, rustdesk_id: str, password: str) -> None:
        cfg = self._support_cfg
        if cfg is None:
            return
        worker = _NotifyWorker(
            webhook_url=cfg.discord_webhook.strip(),
            mention=cfg.mention or "",
            rustdesk_id=rustdesk_id,
            password=password,
            user_email=self._user_email or "(unknown)",
            user_name=self._user_name or "(unknown)",
            parent=self,
        )
        worker.succeeded.connect(lambda: self._on_notify_ok(rustdesk_id, password))
        worker.failed.connect(lambda err: self._on_notify_failed(err, rustdesk_id, password))
        worker.finished.connect(self._cleanup_notify_worker)
        self._notify_worker = worker
        worker.start()

    def _on_notify_ok(self, rustdesk_id: str, password: str) -> None:
        log.info("Support request sent (id=%s)", rustdesk_id)

    def _on_notify_failed(self, error: str, rustdesk_id: str, password: str) -> None:
        log.warning("Notify failed (id=%s): %s", rustdesk_id, error)

    # ── UI helpers ────────────────────────────────────────────────

    def _confirm(self) -> bool:
        box = QMessageBox(self._parent)
        box.setIcon(QMessageBox.Icon.Question)
        box.setWindowTitle(SUPPORT_DIALOG_TITLE)
        box.setText(SUPPORT_DIALOG_BODY)
        send_btn = box.addButton(SUPPORT_CONFIRM_SEND, QMessageBox.ButtonRole.AcceptRole)
        box.addButton(DIALOG_CANCEL, QMessageBox.ButtonRole.RejectRole)
        box.exec()
        return box.clickedButton() is send_btn

    def _error(self, message: str) -> None:
        QMessageBox.warning(self._parent, DIALOG_ERROR_TITLE, message)

    # ── Cleanup ───────────────────────────────────────────────────

    def _cleanup_install_worker(self) -> None:
        worker = self._install_worker
        self._install_worker = None
        if worker is not None:
            worker.deleteLater()

    def _cleanup_launch_worker(self) -> None:
        worker = self._launch_worker
        self._launch_worker = None
        if worker is not None:
            worker.deleteLater()

    def _cleanup_notify_worker(self) -> None:
        worker = self._notify_worker
        self._notify_worker = None
        if worker is not None:
            worker.deleteLater()
