from __future__ import annotations

import logging
import subprocess
from pathlib import Path

from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QColor, QLinearGradient, QPainter, QPen, QPixmap
from PyQt6.QtWidgets import (
    QCheckBox, QComboBox, QFileDialog, QFrame, QHBoxLayout, QLabel,
    QLineEdit, QPlainTextEdit, QPushButton, QVBoxLayout, QWidget,
)

from ...core.config import AppConfig, Game
from ...core.local_config import LocalConfig
from ...resources.strings_vi import (
    ACTION_BROWSE, ACTION_DOWNLOAD, ACTION_LAUNCH_GAME,
    ACTION_UPDATE, DIALOG_ERROR_TITLE,
)
from ...widgets.drop_zone import DropZone
from .image_loader import ImageLoader
from .models import InstallRegistry, InstallStatus
from .trailer_popup import TrailerPopup

log = logging.getLogger(__name__)

_TAG_COLORS: dict[str, str] = {
    "HOT":  "#ff5b3c",
    "GOTY": "#ffd700",
    "NEW":  "#4dffaa",
    "UPD":  "#4f7cff",
    "BEST": "#b48bff",
    "FIX":  "#ffc04d",
}


# ─────────────────────────────────────────────────────────────────────
# Cinematic full-bleed hero with crop-bracket markers
# ─────────────────────────────────────────────────────────────────────
class _DetailHero(QFrame):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("DetailHero")
        self.setFixedHeight(260)
        self._pixmap: QPixmap | None = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(36, 24, 36, 26)
        layout.setSpacing(0)

        # Top row: status pill (right-aligned)
        top = QHBoxLayout()
        top.setContentsMargins(0, 0, 0, 0)
        top.addStretch(1)
        self._status_lbl = QLabel(self)
        self._status_lbl.hide()
        top.addWidget(self._status_lbl)
        layout.addLayout(top)

        layout.addStretch(1)

        # Bottom block: tag, title, meta
        self._tag_lbl = QLabel(self)
        self._tag_lbl.hide()
        layout.addWidget(self._tag_lbl)

        self._title_lbl = QLabel(self)
        self._title_lbl.setObjectName("DetailHeroTitle")
        self._title_lbl.setWordWrap(True)
        layout.addWidget(self._title_lbl)

        self._meta_lbl = QLabel(self)
        self._meta_lbl.setObjectName("HeroMeta")
        layout.addWidget(self._meta_lbl)

    def set_data(
        self,
        title: str,
        tag: str,
        meta: str,
        status: str,
        status_color: str,
    ) -> None:
        self._title_lbl.setText(title.upper())
        if tag:
            color = _TAG_COLORS.get(tag, "#d8ff3a")
            self._tag_lbl.setText(f"[ {tag} ]")
            self._tag_lbl.setStyleSheet(
                f"font-family:'Cascadia Mono',Consolas,monospace;"
                f"color:{color};font-size:11px;font-weight:700;"
                f"letter-spacing:1.5px;padding-bottom:6px;"
            )
            self._tag_lbl.show()
        else:
            self._tag_lbl.hide()
        self._meta_lbl.setText(meta)
        if status:
            self._status_lbl.setText(f"●  {status}")
            self._status_lbl.setStyleSheet(
                f"font-family:'Cascadia Mono',Consolas,monospace;"
                f"background:rgba(7,7,10,0.65);"
                f"color:{status_color};border:1px solid {status_color};"
                f"padding:5px 12px;font-size:10px;font-weight:700;letter-spacing:1.4px;"
            )
            self._status_lbl.show()
        else:
            self._status_lbl.hide()

    def set_image(self, pixmap: QPixmap) -> None:
        self._pixmap = pixmap
        self.update()

    def clear_image(self) -> None:
        self._pixmap = None
        self.update()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.rect()

        painter.fillRect(rect, QColor("#0a0a0e"))

        if self._pixmap and not self._pixmap.isNull():
            scaled = self._pixmap.scaledToWidth(
                rect.width(), Qt.TransformationMode.SmoothTransformation
            )
            img_rect = scaled.rect()
            img_rect.moveTop(-(scaled.height() - rect.height()) // 2)
            img_rect.moveLeft(0)
            painter.drawPixmap(img_rect, scaled)

            # Vertical gradient: lighter top, opaque bottom (for text)
            grad = QLinearGradient(0, 0, 0, rect.height())
            grad.setColorAt(0.0, QColor(7, 7, 10, 70))
            grad.setColorAt(0.35, QColor(7, 7, 10, 95))
            grad.setColorAt(0.65, QColor(7, 7, 10, 200))
            grad.setColorAt(1.0, QColor(7, 7, 10, 252))
            painter.fillRect(rect, grad)

            # Left-side accent fade (extra readability for title)
            lgrad = QLinearGradient(0, 0, rect.width() * 0.4, 0)
            lgrad.setColorAt(0.0, QColor(7, 7, 10, 160))
            lgrad.setColorAt(1.0, QColor(7, 7, 10, 0))
            painter.fillRect(rect, lgrad)

        # Border
        painter.setPen(QPen(QColor("#24242f"), 1))
        painter.drawRect(rect.adjusted(0, 0, -1, -1))

        # Crop-bracket corner marks (lime)
        painter.setPen(QPen(QColor("#d8ff3a"), 2))
        L = 28
        T = 4
        # top-left
        painter.drawLine(rect.left() + T, rect.top() + T, rect.left() + T + L, rect.top() + T)
        painter.drawLine(rect.left() + T, rect.top() + T, rect.left() + T, rect.top() + T + L)
        # top-right
        painter.drawLine(rect.right() - T - L, rect.top() + T, rect.right() - T, rect.top() + T)
        painter.drawLine(rect.right() - T, rect.top() + T, rect.right() - T, rect.top() + T + L)
        # bottom-left
        painter.drawLine(rect.left() + T, rect.bottom() - T - L, rect.left() + T, rect.bottom() - T)
        painter.drawLine(rect.left() + T, rect.bottom() - T, rect.left() + T + L, rect.bottom() - T)
        # bottom-right
        painter.drawLine(rect.right() - T - L, rect.bottom() - T, rect.right() - T, rect.bottom() - T)
        painter.drawLine(rect.right() - T, rect.bottom() - T - L, rect.right() - T, rect.bottom() - T)

        painter.end()


# ─────────────────────────────────────────────────────────────────────
# GameDetailPage — mission briefing layout
# ─────────────────────────────────────────────────────────────────────
class GameDetailPage(QWidget):
    download_requested = pyqtSignal(object, str, int)  # Game, install_path, url_index
    back_requested = pyqtSignal()

    def __init__(self, registry: InstallRegistry, parent=None) -> None:
        super().__init__(parent)
        self._registry = registry
        self._local = LocalConfig()
        self._entries: list[Game] = []
        self._game: Game | None = None
        self._slideshow_urls: list[str] = []
        self._slide_idx = 0
        self._slide_timer = QTimer(self)
        self._slide_timer.setInterval(4000)
        self._slide_timer.timeout.connect(self._advance_slide)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # ── Top bar (back + entry id) ───────────────────────────
        topbar = QHBoxLayout()
        topbar.setContentsMargins(28, 12, 28, 6)
        back_btn = QPushButton("◄  QUAY LẠI", self)
        back_btn.setObjectName("BackButton")
        back_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        back_btn.clicked.connect(self.back_requested)
        topbar.addWidget(back_btn)
        topbar.addStretch(1)
        self._entry_lbl = QLabel("// OPS · ENTRY ----", self)
        self._entry_lbl.setObjectName("PageSection")
        topbar.addWidget(self._entry_lbl)
        outer.addLayout(topbar)

        # ── Hero ────────────────────────────────────────────────
        self._hero = _DetailHero(self)
        outer.addWidget(self._hero)

        # ── Body ────────────────────────────────────────────────
        body = QWidget(self)
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(28, 18, 28, 16)
        body_layout.setSpacing(12)

        # Two-column control row: VARIANT + INSTALL DIR
        controls = QHBoxLayout()
        controls.setSpacing(20)

        # Variant column
        var_col = QVBoxLayout()
        var_col.setSpacing(6)
        var_lbl = QLabel("// VARIANT  ·  BẢN MOD", self)
        var_lbl.setObjectName("DetailSectionLabel")
        var_col.addWidget(var_lbl)
        self._mod_combo = QComboBox(self)
        self._mod_combo.setObjectName("DetailCombo")
        self._mod_combo.setMinimumHeight(36)
        self._mod_combo.currentIndexChanged.connect(self._on_variant_changed)
        var_col.addWidget(self._mod_combo)
        controls.addLayout(var_col, 1)

        # Install path column
        path_col = QVBoxLayout()
        path_col.setSpacing(6)
        path_lbl = QLabel("// INSTALL DIRECTORY  ·  THƯ MỤC CÀI", self)
        path_lbl.setObjectName("DetailSectionLabel")
        path_col.addWidget(path_lbl)
        path_input_row = QHBoxLayout()
        path_input_row.setSpacing(6)
        self._path_edit = QLineEdit(self)
        self._path_edit.setPlaceholderText("Chọn thư mục cài đặt...")
        self._path_edit.setMinimumHeight(36)
        self._path_edit.textChanged.connect(self._update_launch_state)
        path_input_row.addWidget(self._path_edit, 1)
        browse_btn = QPushButton(ACTION_BROWSE.upper(), self)
        browse_btn.setMinimumHeight(36)
        browse_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        browse_btn.clicked.connect(self._on_browse)
        path_input_row.addWidget(browse_btn)
        path_col.addLayout(path_input_row)

        # Defender exclusion opt-in. Checked → on download click we ensure the
        # destination is on Defender's `ExclusionPath` list (skipped silently
        # when an ancestor entry already covers it).
        from ...resources.strings_vi import DEFENDER_CHECKBOX, DEFENDER_TOOLTIP
        self._defender_chk = QCheckBox(DEFENDER_CHECKBOX, self)
        self._defender_chk.setObjectName("DetailDefenderToggle")
        self._defender_chk.setToolTip(DEFENDER_TOOLTIP)
        self._defender_chk.setChecked(False)
        path_col.addWidget(self._defender_chk)

        controls.addLayout(path_col, 2)

        body_layout.addLayout(controls)

        # Drop zone (slim)
        drop = DropZone("⊕  KÉO THẢ THƯ MỤC GAME VÀO ĐÂY", parent=self)
        drop.setMinimumHeight(56)
        drop.setMaximumHeight(56)
        drop.folder_dropped.connect(self._path_edit.setText)
        body_layout.addWidget(drop)

        # Path guide
        guide_lbl = QLabel("// PATH GUIDE  ·  HƯỚNG DẪN", self)
        guide_lbl.setObjectName("DetailSectionLabel")
        body_layout.addWidget(guide_lbl)
        self._guide = QPlainTextEdit(self)
        self._guide.setObjectName("DetailGuide")
        self._guide.setReadOnly(True)
        self._guide.setMinimumHeight(110)
        self._guide.setPlaceholderText("// no path guide provided")
        body_layout.addWidget(self._guide, 1)

        # Action bar
        actions = QHBoxLayout()
        actions.setSpacing(10)
        self._dl_btn = QPushButton("►  " + ACTION_DOWNLOAD.upper(), self)
        self._dl_btn.setObjectName("Accent")
        self._dl_btn.setMinimumHeight(48)
        self._dl_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._dl_btn.clicked.connect(self._on_download)
        actions.addWidget(self._dl_btn, 2)

        self._launch_btn = QPushButton("►  " + ACTION_LAUNCH_GAME.upper(), self)
        self._launch_btn.setObjectName("HeroSecondary")
        self._launch_btn.setMinimumHeight(48)
        self._launch_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._launch_btn.setEnabled(False)
        self._launch_btn.clicked.connect(self._on_launch)
        actions.addWidget(self._launch_btn, 1)

        # Launcher picker — lets the user override `game.launch_file` per
        # install so the Play button can launch a custom shortcut, modded
        # exe, or third-party wrapper. The override is persisted via
        # LocalConfig.set_game_launcher(game.id, relative_path).
        from ...resources.strings_vi import ACTION_SET_LAUNCHER
        self._launcher_pick_btn = QPushButton("⚙", self)
        self._launcher_pick_btn.setObjectName("HeroSecondary")
        self._launcher_pick_btn.setMinimumHeight(48)
        self._launcher_pick_btn.setMaximumWidth(56)
        self._launcher_pick_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._launcher_pick_btn.setToolTip(ACTION_SET_LAUNCHER)
        self._launcher_pick_btn.clicked.connect(self._on_pick_launcher)
        actions.addWidget(self._launcher_pick_btn)

        body_layout.addLayout(actions)

        outer.addWidget(body, 1)

        # ── Trailer popup (floating overlay, child of this page) ───
        self._trailer = TrailerPopup(self)

    # ── public ────────────────────────────────────────────────────

    def show_game(
        self,
        entries: list[Game] | Game,
        config: AppConfig | None = None,
    ) -> None:
        if isinstance(entries, Game):
            entries = [entries]
        if not entries:
            return
        self._entries = entries
        self._slide_timer.stop()
        self._slideshow_urls = []
        self._slide_idx = 0
        self._hero.clear_image()

        canonical = entries[0].game or entries[0].name

        # Aggregate status across variants
        statuses = [self._registry.status_for(g) for g in entries]
        if any(s == InstallStatus.INSTALLED for s in statuses):
            status_word, status_color = "INSTALLED", "#4dffaa"
        elif any(s == InstallStatus.UPDATE for s in statuses):
            status_word, status_color = "UPDATE AVAILABLE", "#ffc04d"
        else:
            status_word, status_color = "NOT INSTALLED", "#5e5e62"

        # Tag
        tag_text = ""
        for e in entries:
            if e.tag and e.tag.upper() in _TAG_COLORS:
                tag_text = e.tag.upper()
                break

        # Meta
        version = next((e.version for e in entries if e.version), "")
        types = sorted({(e.type or "zip").upper() for e in entries})
        meta_parts = [f"{len(entries):02d} BẢN"]
        if version:
            meta_parts.append(f"v{version.lstrip('v')}")
        if types:
            meta_parts.append("/".join(types))
        meta_parts.append(f"WGZ-{(entries[0].id or '0000').upper()}")
        meta_text = "   ·   ".join(meta_parts)

        self._hero.set_data(canonical, tag_text, meta_text, status_word, status_color)

        # Entry ID label in topbar
        eid = (entries[0].id or "0000").upper().zfill(4)
        self._entry_lbl.setText(f"// OPS · ENTRY {eid}")

        # Hero image / slideshow — look up theme by canonical name
        theme = None
        if config:
            theme = config.themes.get(canonical)
            if theme is None:
                for e in entries:
                    theme = config.themes.get(e.game) or config.themes.get(e.name)
                    if theme:
                        break
            if theme:
                if theme.slideshow:
                    self._slideshow_urls = list(theme.slideshow)
                    ImageLoader.instance().request(theme.slideshow[0], self._hero.set_image)
                    if len(theme.slideshow) > 1:
                        self._slide_timer.start()
                elif theme.image:
                    ImageLoader.instance().request(theme.image, self._hero.set_image)

        # Trailer popup — show only if theme has a trailer_url
        trailer_url = (theme.trailer_url if theme else "") or ""
        if trailer_url:
            self._trailer.reset_position()
            self._trailer.play(trailer_url)
        else:
            self._trailer.stop()
            self._trailer.hide()

        # Variant combo — one row per mod. Multi-URL entries are a single
        # multi-part archive (download_progress_page fetches every URL
        # sequentially regardless of the picked index), so we no longer
        # expose the parts as separate selectable rows.
        self._mod_combo.blockSignals(True)
        self._mod_combo.clear()
        for entry in entries:
            parts = len(entry.urls) if entry.urls and len(entry.urls) > 1 else 0
            label = f"{entry.name}   ·   {parts} PHẦN" if parts else entry.name
            self._mod_combo.addItem(label, userData=(entry, 0))
        self._mod_combo.blockSignals(False)
        self._mod_combo.setCurrentIndex(0)
        self._apply_variant(0)

    # ── internal ──────────────────────────────────────────────────

    def _on_variant_changed(self, index: int) -> None:
        if index >= 0:
            self._apply_variant(index)

    def _apply_variant(self, index: int) -> None:
        data = self._mod_combo.itemData(index)
        if not data:
            return
        entry, _url_idx = data
        self._game = entry
        self._guide.setPlainText(entry.path_guide or "")
        saved = self._local.get_game_path(entry.id) or self._local.last_used_folder or ""
        self._path_edit.setText(saved)
        self._update_dl_button()
        self._update_launch_state()

    def _advance_slide(self) -> None:
        if not self._slideshow_urls:
            return
        self._slide_idx = (self._slide_idx + 1) % len(self._slideshow_urls)
        ImageLoader.instance().request(self._slideshow_urls[self._slide_idx], self._hero.set_image)

    def _update_dl_button(self) -> None:
        if not self._game:
            return
        status = self._registry.status_for(self._game)
        word = ACTION_UPDATE if status == InstallStatus.UPDATE else ACTION_DOWNLOAD
        self._dl_btn.setText("►  " + word.upper())

    def _update_launch_state(self) -> None:
        if not self._game:
            self._launch_btn.setEnabled(False)
            return
        path_str = self._path_edit.text().strip()
        launch_rel = (
            self._local.get_game_launcher(self._game.id) or self._game.launch_file
        )
        if path_str and launch_rel:
            launch_abs = Path(path_str) / launch_rel
            self._launch_btn.setEnabled(launch_abs.exists())
        else:
            self._launch_btn.setEnabled(False)

    def _on_browse(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Chọn thư mục cài đặt")
        if folder:
            self._path_edit.setText(folder)

    def _on_download(self) -> None:
        if not self._game:
            return
        path = self._path_edit.text().strip()
        if not path:
            from ...widgets.dialogs import wgz_warn
            wgz_warn(self, "Chọn đường dẫn", "Vui lòng chọn thư mục cài đặt trước.")
            return
        self._local.set_game_path(self._game.id, path)
        self._local.last_used_folder = path
        self._local.save()

        if self._defender_chk.isChecked():
            self._maybe_add_defender_exclusion(Path(path))

        data = self._mod_combo.itemData(self._mod_combo.currentIndex())
        url_idx = data[1] if data else 0
        self.download_requested.emit(self._game, path, url_idx)

    def _maybe_add_defender_exclusion(self, dest: Path) -> None:
        """Add `dest` to Windows Defender's `ExclusionPath` when not covered.

        Failures (UAC dismissed, PowerShell error, Defender disabled) are
        surfaced as a one-shot warning dialog but do NOT block the download —
        the user already committed to the operation by clicking Download.
        """
        from ...core import defender
        from ...resources.strings_vi import (
            DEFENDER_ADD_FAILED, DEFENDER_ADDED, DEFENDER_ALREADY_COVERED,
        )
        try:
            existing = defender.list_exclusions()
        except Exception:
            log.exception("Defender list_exclusions raised")
            existing = []

        if defender.is_covered(dest, existing):
            log.info("Defender exclusion already covers %s", dest)
            self._toast(DEFENDER_ALREADY_COVERED)
            return

        ok, err = defender.add_exclusion_with_uac(dest)
        if ok:
            self._toast(DEFENDER_ADDED)
        else:
            log.warning("Defender exclusion add failed: %s", err)
            self._toast(DEFENDER_ADD_FAILED.format(error=err or "unknown"))

    def _toast(self, message: str) -> None:
        """Lightweight, non-blocking status nudge — currently logged + status bar.

        We deliberately avoid QMessageBox here so the download flow stays
        non-modal; a stronger toast widget can swap in later without touching
        callers.
        """
        log.info("[defender] %s", message)
        # If a status strip is wired up further down the tree it picks the
        # message up via the standard log → status bridge already in place.

    def _on_pick_launcher(self) -> None:
        """Pick (or change) the launcher file used by the Play button.

        Stored as a path *relative to* the install folder so the override is
        portable across drive moves. Files outside the install folder are
        rejected — letting them through would silently break `Launch` after
        a folder rename.
        """
        from ...resources.strings_vi import (
            DIALOG_PICK_LAUNCHER, LAUNCHER_NEED_INSTALL_PATH,
            LAUNCHER_OUTSIDE_INSTALL, LAUNCHER_PICK_FILTER, LAUNCHER_SAVED,
        )
        from ...widgets.dialogs import wgz_warn, wgz_info
        if not self._game:
            return
        install_path_str = self._path_edit.text().strip()
        if not install_path_str:
            wgz_warn(self, "Chọn đường dẫn", LAUNCHER_NEED_INSTALL_PATH)
            return

        install_dir = Path(install_path_str)
        start_dir = str(install_dir) if install_dir.exists() else ""
        # Prefer the currently configured launcher's directory so the user
        # lands near the existing choice on the second pick.
        current_rel = self._local.get_game_launcher(self._game.id) or self._game.launch_file
        if current_rel:
            current_abs = install_dir / current_rel
            if current_abs.exists():
                start_dir = str(current_abs.parent)

        picked, _ = QFileDialog.getOpenFileName(
            self, DIALOG_PICK_LAUNCHER, start_dir, LAUNCHER_PICK_FILTER,
        )
        if not picked:
            return

        picked_abs = Path(picked).resolve()
        try:
            install_abs = install_dir.resolve()
        except Exception:
            install_abs = install_dir

        try:
            rel = picked_abs.relative_to(install_abs)
        except ValueError:
            wgz_warn(
                self,
                "File ngoài thư mục cài đặt",
                LAUNCHER_OUTSIDE_INSTALL.format(install_path=str(install_abs)),
            )
            return

        rel_str = str(rel)
        self._local.set_game_launcher(self._game.id, rel_str)
        self._local.save()
        wgz_info(self, "Đã lưu", LAUNCHER_SAVED.format(file=rel_str))
        self._update_launch_state()

    def _on_launch(self) -> None:
        if not self._game:
            return
        path_str = self._path_edit.text().strip()
        launch_rel = (
            self._local.get_game_launcher(self._game.id) or self._game.launch_file
        )
        if not path_str or not launch_rel:
            return
        launch_abs = Path(path_str) / launch_rel
        if launch_abs.exists():
            try:
                subprocess.Popen([str(launch_abs)], cwd=str(launch_abs.parent))
            except Exception as exc:
                log.exception("Launch failed")
                from ...widgets.dialogs import wgz_error
                wgz_error(self, DIALOG_ERROR_TITLE, f"Không thể chạy game: {exc}")

    # ── trailer popup lifecycle ───────────────────────────────────

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        if getattr(self, "_trailer", None):
            self._trailer.parent_resized()

    def hideEvent(self, event) -> None:
        super().hideEvent(event)
        if getattr(self, "_trailer", None):
            self._trailer.stop()
            self._trailer.hide()
