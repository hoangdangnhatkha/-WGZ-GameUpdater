"""Tab 3 — Config Manager.

Card-grid browser + modal editors. Manages two source files:
    - `CapNhatNightReignMod.json` — list of game mods (id → mod dict)
    - `game_themes.json`         — theme key → hero image / slideshow / trailer

The mods browser groups cards by the mod's `game` field (which usually matches a
theme key). The themes browser shows a lazy-fetched hero thumb per theme.

User flow:
    1. Click a card  → modal opens for edit.
    2. Click "+ NEW" → modal opens with blank form.
    3. Save in modal → in-memory state updated, dirty flag set.
    4. Click "ĐẨY"   → preview dialog, then bulk push to server.

UX features:
    - Per-row dirty marker, header dirty-count chip.
    - Toast undo ribbon for deletes (8s).
    - Autosaved draft persists across crashes; restore prompt on next load.
    - Theme key rename cascades to all mods referencing it.
    - Validation in modal: inline errors near each invalid field.
    - Lazy thumbnail loader with in-memory + on-disk cache.
"""

from __future__ import annotations

import copy
import hashlib
import json
import logging
from datetime import datetime
from typing import Any, Callable

from PyQt6.QtCore import (
    QObject,
    QPoint,
    QSize,
    Qt,
    QThread,
    QTimer,
    QUrl,
    pyqtSignal,
)
from PyQt6.QtGui import QIntValidator, QKeySequence, QPixmap, QShortcut
from PyQt6.QtNetwork import QNetworkAccessManager, QNetworkReply, QNetworkRequest
from PyQt6.QtWidgets import (
    QButtonGroup,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMenu,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QScrollArea,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from ...core import api_client
from ...core.paths import (
    CONFIG_BUNDLED,
    CONFIG_LOCAL,
    THEMES_BUNDLED_CANDIDATES,
    THEMES_LOCAL,
    USER_DATA_DIR,
)
from ...widgets.loading_dialog import LoadingDialog
from .github_writer import PushConfigWorker

log = logging.getLogger(__name__)

_RESERVED_GAME_KEYS = {"updater", "game_themes.json"}
_TYPE_CHOICES = ("zip", "rar", "exe")
_AUTOSAVE_DEBOUNCE_MS = 1500
_UNDO_TIMEOUT_MS = 8000
_THUMB_DIR_NAME = "theme_thumb_cache"
_THUMB_W, _THUMB_H = 320, 96


# ════════════════════════════════════════════════════════════════════
# Workers + I/O helpers
# ════════════════════════════════════════════════════════════════════

class _ConfigLoadWorker(QThread):
    finished_ok = pyqtSignal(dict, dict)
    failed = pyqtSignal(str)

    def __init__(self, prefer_remote: bool, parent=None) -> None:
        super().__init__(parent)
        self._prefer_remote = prefer_remote

    def run(self) -> None:
        try:
            games_raw = _load_games_raw(self._prefer_remote) or {}
            themes_raw = _load_themes_raw(self._prefer_remote) or {}
            self.finished_ok.emit(games_raw, themes_raw)
        except Exception as exc:
            log.exception("Config load failed")
            self.failed.emit(str(exc))


def _read_json(*candidates) -> dict:
    for path in candidates:
        if path and path.exists():
            try:
                return json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                log.exception("Read failed: %s", path)
    return {}


def _fetch_api_config() -> dict | None:
    try:
        return api_client.get_config()
    except Exception as exc:
        log.warning("API config fetch failed; using local cache (%s)", exc)
        return None


def _load_games_raw(prefer_remote: bool) -> dict:
    if prefer_remote:
        raw = _fetch_api_config()
        if isinstance(raw, dict):
            return {k: v for k, v in raw.items() if k != "game_themes.json"}
    return _read_json(CONFIG_LOCAL, CONFIG_BUNDLED)


def _load_themes_raw(prefer_remote: bool) -> dict:
    if prefer_remote:
        raw = _fetch_api_config()
        if isinstance(raw, dict):
            themes = raw.get("game_themes.json")
            if isinstance(themes, dict):
                return themes
    return _read_json(THEMES_LOCAL, *THEMES_BUNDLED_CANDIDATES)


def _draft_path():
    return USER_DATA_DIR / "manager_draft.json"


def _ui_state_path():
    return USER_DATA_DIR / "manager_groups.json"


def _thumb_dir():
    return USER_DATA_DIR / _THUMB_DIR_NAME


# ════════════════════════════════════════════════════════════════════
# Lazy thumbnail loader (Qt network + on-disk cache)
# ════════════════════════════════════════════════════════════════════

class _ThumbnailLoader(QObject):
    """Process-wide thumbnail loader. Caches in memory and on disk."""

    _instance: "_ThumbnailLoader | None" = None

    def __init__(self) -> None:
        super().__init__()
        self._nam = QNetworkAccessManager(self)
        self._memory: dict[str, QPixmap] = {}
        self._pending: dict[str, list[Callable[[QPixmap | None], None]]] = {}

    @classmethod
    def instance(cls) -> "_ThumbnailLoader":
        if cls._instance is None:
            cls._instance = _ThumbnailLoader()
        return cls._instance

    def request(self, url: str, callback: Callable[[QPixmap | None], None]) -> None:
        url = (url or "").strip()
        if not url:
            callback(None)
            return
        if url in self._memory:
            callback(self._memory[url])
            return
        disk = self._read_disk(url)
        if disk is not None:
            self._memory[url] = disk
            callback(disk)
            return
        if url in self._pending:
            self._pending[url].append(callback)
            return
        self._pending[url] = [callback]
        try:
            req = QNetworkRequest(QUrl(url))
            req.setAttribute(QNetworkRequest.Attribute.RedirectPolicyAttribute,
                             QNetworkRequest.RedirectPolicy.NoLessSafeRedirectPolicy)
            req.setRawHeader(b"User-Agent", b"WGZ-Manager")
            reply = self._nam.get(req)
            reply.finished.connect(lambda r=reply, u=url: self._on_reply(u, r))
        except Exception:
            log.exception("Thumb request failed: %s", url)
            self._dispatch(url, None)

    def _on_reply(self, url: str, reply: QNetworkReply) -> None:
        try:
            if reply.error() != QNetworkReply.NetworkError.NoError:
                log.debug("Thumb error %s: %s", url, reply.errorString())
                self._dispatch(url, None)
                return
            data = bytes(reply.readAll())
            pixmap = QPixmap()
            if not pixmap.loadFromData(data):
                self._dispatch(url, None)
                return
            scaled = pixmap.scaled(
                _THUMB_W * 2, _THUMB_H * 2,
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation,
            )
            self._memory[url] = scaled
            self._write_disk(url, data)
            self._dispatch(url, scaled)
        finally:
            reply.deleteLater()

    def _dispatch(self, url: str, pixmap: QPixmap | None) -> None:
        callbacks = self._pending.pop(url, [])
        for cb in callbacks:
            try:
                cb(pixmap)
            except RuntimeError:
                # Receiver widget was destroyed before delivery (rebuild raced).
                pass
            except Exception:
                log.exception("Thumb callback failed")

    def _disk_path(self, url: str):
        h = hashlib.sha1(url.encode("utf-8")).hexdigest()
        return _thumb_dir() / f"{h}.bin"

    def _read_disk(self, url: str) -> QPixmap | None:
        p = self._disk_path(url)
        if not p.exists():
            return None
        try:
            data = p.read_bytes()
            pixmap = QPixmap()
            if pixmap.loadFromData(data):
                return pixmap.scaled(
                    _THUMB_W * 2, _THUMB_H * 2,
                    Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                    Qt.TransformationMode.SmoothTransformation,
                )
        except Exception:
            log.exception("Thumb disk read failed: %s", p)
        return None

    def _write_disk(self, url: str, data: bytes) -> None:
        try:
            d = _thumb_dir()
            d.mkdir(parents=True, exist_ok=True)
            self._disk_path(url).write_bytes(data)
        except Exception:
            log.exception("Thumb disk write failed: %s", url)


# ════════════════════════════════════════════════════════════════════
# Shared widgets
# ════════════════════════════════════════════════════════════════════

class _Section(QFrame):
    """Collapsible form section."""

    toggled = pyqtSignal(str, bool)

    def __init__(self, section_id: str, caption: str, *,
                 expanded: bool = True, required: bool = False,
                 parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._section_id = section_id
        self._expanded = expanded
        self.setObjectName("MgrSection")

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self._header = QFrame(self)
        self._header.setObjectName("MgrSectionHeader")
        self._header.setCursor(Qt.CursorShape.PointingHandCursor)
        h = QHBoxLayout(self._header)
        h.setContentsMargins(0, 6, 0, 6)
        h.setSpacing(8)

        self._chev = QLabel("▾" if expanded else "▸", self._header)
        self._chev.setObjectName("MgrSectionChevron")
        self._chev.setFixedWidth(12)
        h.addWidget(self._chev)

        label = caption + (" *" if required else "")
        self._caption = QLabel(label, self._header)
        self._caption.setObjectName("MgrSectionCaption")
        h.addWidget(self._caption, 1)

        self._summary = QLabel("", self._header)
        self._summary.setObjectName("MgrSectionSummary")
        self._summary.setVisible(False)
        h.addWidget(self._summary)

        self._header.mousePressEvent = self._on_header_clicked  # type: ignore
        root.addWidget(self._header)

        self._body = QFrame(self)
        self._body.setObjectName("MgrSectionBody")
        self._body_layout = QVBoxLayout(self._body)
        self._body_layout.setContentsMargins(0, 2, 0, 10)
        self._body_layout.setSpacing(10)
        root.addWidget(self._body)
        self._body.setVisible(expanded)

    def add(self, item) -> None:
        if isinstance(item, QWidget):
            self._body_layout.addWidget(item)
        else:
            self._body_layout.addLayout(item)

    def set_expanded(self, expanded: bool) -> None:
        if expanded == self._expanded:
            return
        self._expanded = expanded
        self._chev.setText("▾" if expanded else "▸")
        self._body.setVisible(expanded)
        self.toggled.emit(self._section_id, expanded)

    def set_summary(self, text: str) -> None:
        self._summary.setText(text)
        self._summary.setVisible(bool(text))

    def _on_header_clicked(self, event):  # noqa: N802
        if event.button() == Qt.MouseButton.LeftButton:
            self.set_expanded(not self._expanded)


class _UrlListEditor(QFrame):
    """List of URL rows with add/remove buttons + index labels."""

    changed = pyqtSignal()

    def __init__(self, caption: str = "", placeholder: str = "https://...",
                 *, show_caption: bool = False, add_label: str = "+ THÊM",
                 parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("MgrUrlListWrap")
        self._placeholder = placeholder
        self._rows: list[tuple[QLineEdit, QPushButton, QLabel]] = []

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(6)

        head = QHBoxLayout()
        head.setContentsMargins(0, 0, 0, 0)
        if show_caption and caption:
            cap = QLabel(caption, self)
            cap.setObjectName("MgrSectionCaption")
            head.addWidget(cap)
        head.addStretch(1)
        add = QPushButton(add_label, self)
        add.setObjectName("MgrAddBtn")
        add.setCursor(Qt.CursorShape.PointingHandCursor)
        add.clicked.connect(lambda: (self._add_row(""), self.changed.emit()))
        head.addWidget(add)
        root.addLayout(head)

        self._rows_host = QFrame(self)
        self._rows_host.setObjectName("MgrUrlRowsHost")
        self._rows_layout = QVBoxLayout(self._rows_host)
        self._rows_layout.setContentsMargins(0, 0, 0, 0)
        self._rows_layout.setSpacing(4)
        root.addWidget(self._rows_host)

    def set_values(self, values: list[str]) -> None:
        while self._rows:
            edit, btn, idx_lbl = self._rows.pop()
            edit.deleteLater()
            btn.deleteLater()
            idx_lbl.deleteLater()
        for i in reversed(range(self._rows_layout.count())):
            item = self._rows_layout.takeAt(i)
            w = item.widget()
            if w is not None:
                w.deleteLater()
        for v in values:
            self._add_row(v, emit=False)
        if not values:
            self._add_row("", emit=False)

    def values(self) -> list[str]:
        return [e.text().strip() for e, _, _ in self._rows if e.text().strip()]

    def count_non_empty(self) -> int:
        return sum(1 for e, _, _ in self._rows if e.text().strip())

    def _add_row(self, initial: str, *, emit: bool = True) -> None:
        row = QFrame(self._rows_host)
        row.setObjectName("MgrUrlRow")
        lay = QHBoxLayout(row)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(6)

        idx_lbl = QLabel(self)
        idx_lbl.setObjectName("MgrUrlIndex")
        idx_lbl.setFixedWidth(28)
        idx_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(idx_lbl)

        edit = QLineEdit(initial, self)
        edit.setObjectName("MgrInput")
        edit.setPlaceholderText(self._placeholder)
        edit.textEdited.connect(self.changed)
        lay.addWidget(edit, 1)

        rm = QPushButton("✕", self)
        rm.setObjectName("MgrRemoveBtn")
        rm.setFixedWidth(28)
        rm.setCursor(Qt.CursorShape.PointingHandCursor)
        rm.clicked.connect(lambda: self._remove_row(row, edit, rm, idx_lbl))
        lay.addWidget(rm)

        self._rows_layout.addWidget(row)
        self._rows.append((edit, rm, idx_lbl))
        self._renumber()
        if emit:
            self.changed.emit()

    def _remove_row(self, row, edit, btn, idx) -> None:
        try:
            self._rows.remove((edit, btn, idx))
        except ValueError:
            return
        row.deleteLater()
        self._renumber()
        self.changed.emit()

    def _renumber(self) -> None:
        for i, (_, _, idx_lbl) in enumerate(self._rows, start=1):
            idx_lbl.setText(f"{i:02d}")


class _SearchBar(QFrame):
    text_changed = pyqtSignal(str)

    def __init__(self, placeholder: str = "Tìm...", parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("MgrSearchWrap")
        lay = QHBoxLayout(self)
        lay.setContentsMargins(8, 0, 6, 0)
        lay.setSpacing(6)
        self._glyph = QLabel("⌕", self)
        self._glyph.setObjectName("MgrSearchGlyph")
        self._glyph.setFixedWidth(14)
        lay.addWidget(self._glyph)
        self._edit = QLineEdit(self)
        self._edit.setObjectName("MgrSearchInput")
        self._edit.setPlaceholderText(placeholder)
        self._edit.textChanged.connect(self._on_text_changed)
        lay.addWidget(self._edit, 1)
        self._clear = QPushButton("✕", self)
        self._clear.setObjectName("MgrSearchClear")
        self._clear.setFixedWidth(20)
        self._clear.setCursor(Qt.CursorShape.PointingHandCursor)
        self._clear.setVisible(False)
        self._clear.clicked.connect(lambda: self._edit.setText(""))
        lay.addWidget(self._clear)
        self._debounce = QTimer(self)
        self._debounce.setSingleShot(True)
        self._debounce.setInterval(180)
        self._debounce.timeout.connect(
            lambda: self.text_changed.emit(self._edit.text().strip())
        )

    def _on_text_changed(self, text: str) -> None:
        self._clear.setVisible(bool(text))
        self._debounce.start()

    def focus_input(self) -> None:
        self._edit.setFocus()
        self._edit.selectAll()


class _FilterChips(QFrame):
    filter_changed = pyqtSignal(str)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("MgrFilterWrap")
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(4)
        self._group = QButtonGroup(self)
        self._group.setExclusive(True)
        self._buttons: dict[str, QPushButton] = {}
        for key, label in (
            ("all", "TẤT CẢ"),
            ("dirty", "CHƯA ĐẨY"),
            ("ungrouped", "CHƯA NHÓM"),
        ):
            btn = QPushButton(label, self)
            btn.setObjectName("MgrFilterChip")
            btn.setCheckable(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda _c, k=key: self.filter_changed.emit(k))
            lay.addWidget(btn)
            self._group.addButton(btn)
            self._buttons[key] = btn
        self._buttons["all"].setChecked(True)

    def current(self) -> str:
        for key, btn in self._buttons.items():
            if btn.isChecked():
                return key
        return "all"


class _UndoRibbon(QFrame):
    undo_clicked = pyqtSignal()
    dismissed = pyqtSignal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("MgrUndoRibbon")
        self.setVisible(False)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(10, 6, 6, 6)
        lay.setSpacing(8)
        self._label = QLabel("", self)
        self._label.setObjectName("MgrUndoText")
        lay.addWidget(self._label, 1)
        self._countdown = QLabel("", self)
        self._countdown.setObjectName("MgrUndoCountdown")
        lay.addWidget(self._countdown)
        self._undo_btn = QPushButton("↶  HOÀN TÁC", self)
        self._undo_btn.setObjectName("MgrUndoBtn")
        self._undo_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._undo_btn.clicked.connect(self._on_undo_clicked)
        lay.addWidget(self._undo_btn)
        self._close_btn = QPushButton("✕", self)
        self._close_btn.setObjectName("MgrUndoClose")
        self._close_btn.setFixedWidth(20)
        self._close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._close_btn.clicked.connect(self._dismiss)
        lay.addWidget(self._close_btn)
        self._tick = QTimer(self)
        self._tick.setInterval(1000)
        self._tick.timeout.connect(self._on_tick)
        self._remaining = 0

    def show_for(self, message: str, seconds: int = _UNDO_TIMEOUT_MS // 1000) -> None:
        self._label.setText(message)
        self._remaining = seconds
        self._countdown.setText(f"{seconds}s")
        self.setVisible(True)
        self._tick.start()

    def _on_undo_clicked(self) -> None:
        self._stop()
        self.undo_clicked.emit()

    def _dismiss(self) -> None:
        if self.isVisible():
            self._stop()
            self.dismissed.emit()

    def _on_tick(self) -> None:
        self._remaining -= 1
        if self._remaining <= 0:
            self._dismiss()
            return
        self._countdown.setText(f"{self._remaining}s")

    def _stop(self) -> None:
        self._tick.stop()
        self.setVisible(False)


# ════════════════════════════════════════════════════════════════════
# Cards
# ════════════════════════════════════════════════════════════════════

class _MetaChip(QLabel):
    def __init__(self, text: str, kind: str = "default", parent=None) -> None:
        super().__init__(text, parent)
        self.setObjectName("MgrChip")
        self.setProperty("kind", kind)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)


class _GameCard(QFrame):
    """Card representing a single mod entry."""

    edit_requested = pyqtSignal(str)        # gid
    menu_requested = pyqtSignal(str, QPoint)  # gid, global pos

    def __init__(self, gid: str, game: dict, dirty: bool, parent=None) -> None:
        super().__init__(parent)
        self._gid = gid
        self.setObjectName("MgrGameCard")
        self.setProperty("dirty", "true" if dirty else "false")
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(14, 10, 12, 10)
        lay.setSpacing(6)

        # Top row
        top = QHBoxLayout()
        top.setSpacing(8)

        self._dirty_dot = QLabel("●", self)
        self._dirty_dot.setObjectName("MgrCardDirtyDot")
        self._dirty_dot.setFixedWidth(10)
        self._dirty_dot.setVisible(dirty)
        top.addWidget(self._dirty_dot)

        self._id_lbl = QLabel(f"#{gid}", self)
        self._id_lbl.setObjectName("MgrCardId")
        top.addWidget(self._id_lbl)

        self._name_lbl = QLabel(game.get("name") or "(không tên)", self)
        self._name_lbl.setObjectName("MgrCardName")
        top.addWidget(self._name_lbl, 1)

        self._edit_btn = QPushButton("✎  SỬA", self)
        self._edit_btn.setObjectName("MgrCardEdit")
        self._edit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._edit_btn.clicked.connect(lambda: self.edit_requested.emit(self._gid))
        top.addWidget(self._edit_btn)

        self._menu_btn = QPushButton("⋮", self)
        self._menu_btn.setObjectName("MgrCardMenu")
        self._menu_btn.setFixedWidth(28)
        self._menu_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._menu_btn.clicked.connect(self._emit_menu)
        top.addWidget(self._menu_btn)

        lay.addLayout(top)

        # Meta row
        meta = QHBoxLayout()
        meta.setSpacing(6)
        meta.setContentsMargins(20, 0, 0, 0)
        self._meta_layout = meta
        self._meta_widgets: list[QWidget] = []
        self._populate_meta(game)
        meta.addStretch(1)
        lay.addLayout(meta)

    def update_state(self, game: dict, dirty: bool) -> None:
        self.setProperty("dirty", "true" if dirty else "false")
        self.style().unpolish(self)
        self.style().polish(self)
        self._dirty_dot.setVisible(dirty)
        self._name_lbl.setText(game.get("name") or "(không tên)")
        for w in self._meta_widgets:
            w.deleteLater()
        self._meta_widgets.clear()
        for i in reversed(range(self._meta_layout.count())):
            item = self._meta_layout.itemAt(i)
            if item is not None and item.widget() is not None:
                pass  # handled via _meta_widgets list
        # Reinsert chips ahead of stretch
        # Clear remaining stretch items by rebuilding
        while self._meta_layout.count():
            item = self._meta_layout.takeAt(0)
            w = item.widget()
            if w is not None:
                w.deleteLater()
        self._populate_meta(game)
        self._meta_layout.addStretch(1)

    def _populate_meta(self, game: dict) -> None:
        version = (game.get("version") or "").strip()
        tp = (game.get("type") or "zip").strip()
        urls = list(game.get("urls") or [])
        if not urls and game.get("url"):
            urls = [str(game["url"])]
        has_pwd = bool((game.get("password") or "").strip())
        launch = bool((game.get("launch_file") or "").strip())
        tag = (game.get("tag") or "").strip()
        chips: list[tuple[str, str]] = []
        if version:
            chips.append((version, "version"))
        if tp:
            chips.append((tp.upper(), "type"))
        chips.append((f"{len(urls)} parts" if urls else "0 parts", "parts"))
        if has_pwd:
            chips.append(("PWD", "flag"))
        if launch:
            chips.append(("LAUNCH ✓", "flag"))
        if tag:
            chips.append((tag.upper(), "tag"))
        for text, kind in chips:
            chip = _MetaChip(text, kind, self)
            self._meta_layout.addWidget(chip)
            self._meta_widgets.append(chip)

    def _emit_menu(self) -> None:
        self.menu_requested.emit(
            self._gid,
            self._menu_btn.mapToGlobal(QPoint(0, self._menu_btn.height())),
        )

    def mousePressEvent(self, event):  # noqa: N802
        if event.button() == Qt.MouseButton.LeftButton:
            self.edit_requested.emit(self._gid)
        elif event.button() == Qt.MouseButton.RightButton:
            self.menu_requested.emit(self._gid, event.globalPosition().toPoint())
        super().mousePressEvent(event)


class _GroupBand(QFrame):
    """Collapsible group header + body holding cards for a single `game` key."""

    toggle_requested = pyqtSignal(str)
    add_requested = pyqtSignal(str)
    menu_requested = pyqtSignal(str, QPoint)

    def __init__(self, key: str, label: str, count: int, dirty_count: int,
                 expanded: bool, parent=None) -> None:
        super().__init__(parent)
        self._key = key
        self.setObjectName("MgrGroupBand")
        self.setProperty("expanded", "true" if expanded else "false")

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Header
        hdr = QFrame(self)
        hdr.setObjectName("MgrGroupBandHeader")
        hdr.setCursor(Qt.CursorShape.PointingHandCursor)
        h = QHBoxLayout(hdr)
        h.setContentsMargins(0, 6, 0, 6)
        h.setSpacing(8)
        self._chev = QLabel("▾" if expanded else "▸", hdr)
        self._chev.setObjectName("MgrGroupChevron")
        self._chev.setFixedWidth(12)
        h.addWidget(self._chev)
        self._name = QLabel(label, hdr)
        self._name.setObjectName("MgrGroupName")
        h.addWidget(self._name, 0)
        self._count = QLabel(f"· {count} mods", hdr)
        self._count.setObjectName("MgrGroupSub")
        h.addWidget(self._count, 1)
        self._dirty = QLabel("●", hdr)
        self._dirty.setObjectName("MgrGroupDirtyDot")
        self._dirty.setVisible(dirty_count > 0)
        self._dirty.setToolTip(f"{dirty_count} mod chưa đẩy")
        h.addWidget(self._dirty)
        self._add_btn = QPushButton("+ Mod vào nhóm", hdr)
        self._add_btn.setObjectName("MgrGroupAddBtn")
        self._add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._add_btn.clicked.connect(lambda: self.add_requested.emit(self._key))
        h.addWidget(self._add_btn)
        self._menu_btn = QPushButton("⋮", hdr)
        self._menu_btn.setObjectName("MgrGroupMenuBtn")
        self._menu_btn.setFixedWidth(28)
        self._menu_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._menu_btn.clicked.connect(self._emit_menu)
        h.addWidget(self._menu_btn)
        hdr.mousePressEvent = self._on_header_clicked  # type: ignore
        root.addWidget(hdr)
        self._hdr = hdr

        # Body
        self._body = QFrame(self)
        self._body.setObjectName("MgrGroupBandBody")
        body_lay = QVBoxLayout(self._body)
        body_lay.setContentsMargins(0, 4, 0, 6)
        body_lay.setSpacing(6)
        root.addWidget(self._body)
        self._body.setVisible(expanded)

    def body_layout(self) -> QVBoxLayout:
        return self._body.layout()  # type: ignore

    def set_expanded(self, expanded: bool) -> None:
        self._chev.setText("▾" if expanded else "▸")
        self._body.setVisible(expanded)
        self.setProperty("expanded", "true" if expanded else "false")
        self.style().unpolish(self)
        self.style().polish(self)

    def set_dirty_count(self, n: int) -> None:
        self._dirty.setVisible(n > 0)
        self._dirty.setToolTip(f"{n} mod chưa đẩy")

    def set_count(self, n: int) -> None:
        self._count.setText(f"· {n} mods")

    def _emit_menu(self) -> None:
        self.menu_requested.emit(
            self._key,
            self._menu_btn.mapToGlobal(QPoint(0, self._menu_btn.height())),
        )

    def _on_header_clicked(self, event):  # noqa: N802
        if event.button() == Qt.MouseButton.LeftButton:
            self.toggle_requested.emit(self._key)


class _ThemeCard(QFrame):
    """Card representing a single theme entry. Shows lazy hero thumbnail."""

    edit_requested = pyqtSignal(str)
    menu_requested = pyqtSignal(str, QPoint)

    def __init__(self, key: str, theme: dict, dirty: bool,
                 mod_count: int, parent=None) -> None:
        super().__init__(parent)
        self._key = key
        self.setObjectName("MgrThemeCard")
        self.setProperty("dirty", "true" if dirty else "false")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(_THUMB_H + 70)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Thumbnail area
        self._thumb = QLabel(self)
        self._thumb.setObjectName("MgrThemeThumb")
        self._thumb.setFixedHeight(_THUMB_H)
        self._thumb.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._thumb.setText("LOADING..." if (theme.get("image") or "").strip() else "NO IMAGE")
        root.addWidget(self._thumb)

        # Meta
        bottom = QFrame(self)
        bottom.setObjectName("MgrThemeMeta")
        b = QVBoxLayout(bottom)
        b.setContentsMargins(12, 8, 8, 8)
        b.setSpacing(6)

        top_row = QHBoxLayout()
        top_row.setSpacing(8)
        self._dirty_dot = QLabel("●", bottom)
        self._dirty_dot.setObjectName("MgrCardDirtyDot")
        self._dirty_dot.setFixedWidth(10)
        self._dirty_dot.setVisible(dirty)
        top_row.addWidget(self._dirty_dot)
        self._name_lbl = QLabel(key, bottom)
        self._name_lbl.setObjectName("MgrCardName")
        top_row.addWidget(self._name_lbl, 1)
        self._menu_btn = QPushButton("⋮", bottom)
        self._menu_btn.setObjectName("MgrCardMenu")
        self._menu_btn.setFixedWidth(28)
        self._menu_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._menu_btn.clicked.connect(self._emit_menu)
        top_row.addWidget(self._menu_btn)
        b.addLayout(top_row)

        chips_row = QHBoxLayout()
        chips_row.setSpacing(6)
        chips_row.setContentsMargins(14, 0, 0, 0)
        has_img = bool((theme.get("image") or "").strip())
        has_trailer = bool((theme.get("trailer_url") or "").strip())
        n_slides = len(theme.get("slideshow") or [])
        chips_row.addWidget(_MetaChip("IMAGE ✓" if has_img else "NO IMAGE",
                                      "version" if has_img else "type", bottom))
        chips_row.addWidget(_MetaChip(f"{n_slides} slides", "parts", bottom))
        if has_trailer:
            chips_row.addWidget(_MetaChip("TRAILER", "flag", bottom))
        chips_row.addWidget(_MetaChip(f"{mod_count} mod" + ("" if mod_count == 1 else "s"),
                                      "tag", bottom))
        chips_row.addStretch(1)
        b.addLayout(chips_row)

        root.addWidget(bottom)

    def load_thumb(self, url: str) -> None:
        if not url:
            self._thumb.setText("NO IMAGE")
            return
        loader = _ThumbnailLoader.instance()
        loader.request(url, self._apply_thumb)

    def _apply_thumb(self, pixmap: QPixmap | None) -> None:
        try:
            if pixmap is None or pixmap.isNull():
                self._thumb.setText("KHÔNG TẢI ĐƯỢC")
                return
            scaled = pixmap.scaled(
                self._thumb.width() or _THUMB_W, _THUMB_H,
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation,
            )
            self._thumb.setPixmap(scaled)
            self._thumb.setText("")
        except RuntimeError:
            # Card destroyed during rebuild before the network reply landed.
            pass

    def _emit_menu(self) -> None:
        self.menu_requested.emit(
            self._key,
            self._menu_btn.mapToGlobal(QPoint(0, self._menu_btn.height())),
        )

    def mousePressEvent(self, event):  # noqa: N802
        if event.button() == Qt.MouseButton.LeftButton:
            self.edit_requested.emit(self._key)
        elif event.button() == Qt.MouseButton.RightButton:
            self.menu_requested.emit(self._key, event.globalPosition().toPoint())
        super().mousePressEvent(event)


# ════════════════════════════════════════════════════════════════════
# Modal: mod editor
# ════════════════════════════════════════════════════════════════════

def _labeled(parent: QWidget, label: str, widget: QWidget, *,
             hint: str | None = None, error: QLabel | None = None) -> QVBoxLayout:
    col = QVBoxLayout()
    col.setContentsMargins(0, 0, 0, 0)
    col.setSpacing(3)
    lbl = QLabel(label, parent)
    lbl.setObjectName("MgrFieldLabel")
    col.addWidget(lbl)
    col.addWidget(widget)
    if hint:
        h = QLabel(hint, parent)
        h.setObjectName("MgrFieldHint")
        h.setWordWrap(True)
        col.addWidget(h)
    if error is not None:
        col.addWidget(error)
    return col


class _GameEditDialog(QDialog):
    """Modal for creating / editing a single mod entry."""

    def __init__(
        self,
        *,
        gid: str | None,
        existing: dict | None,
        theme_keys: list[str],
        theme_image_keys: set[str],
        used_ids: set[str],
        default_group: str = "",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("MgrEditDialog")
        self.setModal(True)
        self.setMinimumSize(720, 640)

        self._editing_existing = existing is not None
        self._original_gid = gid
        self._used_ids = set(used_ids)
        if self._editing_existing and gid:
            self._used_ids.discard(gid)
        self._theme_keys = list(theme_keys)
        self._theme_image_keys = set(theme_image_keys)
        self._initial = copy.deepcopy(existing) if existing else None

        root = QVBoxLayout(self)
        root.setContentsMargins(24, 22, 24, 18)
        root.setSpacing(14)

        # Header
        title_text = "// SỬA MOD" if self._editing_existing else "// MOD MỚI"
        title = QLabel(title_text, self)
        title.setObjectName("MgrDialogTitle")
        root.addWidget(title)
        subtitle_text = (
            f"#{gid} · {(existing or {}).get('name') or '(không tên)'}"
            if self._editing_existing else "Thêm một mod mới vào server."
        )
        self._subtitle = QLabel(subtitle_text, self)
        self._subtitle.setObjectName("MgrDialogSubtitle")
        root.addWidget(self._subtitle)

        # Hero link strip (for game→theme cross-link)
        self._hero = _HeroLinkStrip(self)
        root.addWidget(self._hero)

        # Scrollable form
        scroll = QScrollArea(self)
        scroll.setObjectName("MgrDialogScroll")
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        form_wrap = QWidget()
        form_wrap.setObjectName("MgrFormWrap")
        form = QVBoxLayout(form_wrap)
        form.setContentsMargins(2, 2, 18, 18)
        form.setSpacing(10)
        self._form_wrap = form_wrap

        # § IDENTITY
        sec_id = _Section("identity", "// IDENTITY", expanded=True, parent=form_wrap)
        form.addWidget(sec_id)

        self._field_id = QLineEdit(form_wrap)
        self._field_id.setObjectName("MgrInput")
        self._field_id.setValidator(QIntValidator(1, 999999, self._field_id))
        self._field_id.setPlaceholderText("Số nguyên (vd: 5)")
        self._field_id.textChanged.connect(self._on_anything_changed)
        self._err_id = self._mk_error()
        sec_id.add(_labeled(form_wrap, "ID *", self._field_id,
                            hint="Khoá định danh. Phải là số duy nhất.",
                            error=self._err_id))

        self._field_name = self._mk_input("Tên hiển thị")
        self._err_name = self._mk_error()
        sec_id.add(_labeled(form_wrap, "TÊN *", self._field_name, error=self._err_name))

        self._field_game = QComboBox(form_wrap)
        self._field_game.setObjectName("MgrCombo")
        self._field_game.setEditable(True)
        self._field_game.lineEdit().setPlaceholderText("Chọn key trong Themes hoặc gõ tự do")
        self._field_game.lineEdit().textChanged.connect(self._on_anything_changed)
        self._field_game.lineEdit().textChanged.connect(lambda _t: self._update_hero())
        sec_id.add(_labeled(form_wrap, "GAME", self._field_game,
                            hint="Khớp với key trong Themes (dùng chung hero image)."))

        self._field_version = self._mk_input("vd: v1.4.0")
        sec_id.add(_labeled(form_wrap, "VERSION", self._field_version))

        self._field_tag = QComboBox(form_wrap)
        self._field_tag.setObjectName("MgrCombo")
        # DB constraint `mods_tag_check`: tag IN ('UPD','HOT','GOTY') OR NULL.
        # Empty entry maps to NULL on save; keep the four options in this exact
        # order so the default ("(không có)") wins on blank forms.
        self._field_tag.addItem("(không có)", userData=None)
        for code in ("UPD", "HOT", "GOTY"):
            self._field_tag.addItem(code, userData=code)
        sec_id.add(_labeled(form_wrap, "TAG", self._field_tag,
                            hint="UPD / HOT / GOTY hoặc bỏ trống."))

        # § INSTALL
        sec_in = _Section("install", "// INSTALL", expanded=True, parent=form_wrap)
        form.addWidget(sec_in)
        self._field_type = QComboBox(form_wrap)
        self._field_type.setObjectName("MgrCombo")
        self._field_type.setEditable(True)
        self._field_type.addItems(_TYPE_CHOICES)
        self._field_type.currentTextChanged.connect(self._on_anything_changed)
        sec_in.add(_labeled(form_wrap, "TYPE", self._field_type,
                            hint="zip / rar / exe."))

        self._field_launch = self._mk_input("vd: Game/start.exe")
        sec_in.add(_labeled(form_wrap, "LAUNCH FILE", self._field_launch))

        self._field_password = self._mk_input("vd: daominha.com")
        sec_in.add(_labeled(form_wrap, "PASSWORD", self._field_password,
                            hint="Mật khẩu giải nén (nếu có)."))

        self._field_path_guide = QPlainTextEdit(form_wrap)
        self._field_path_guide.setObjectName("MgrTextArea")
        self._field_path_guide.setFixedHeight(72)
        self._field_path_guide.textChanged.connect(self._on_anything_changed)
        sec_in.add(_labeled(form_wrap, "PATH GUIDE", self._field_path_guide,
                            hint="Hướng dẫn người dùng chọn thư mục cài."))

        # § DOWNLOAD
        sec_dl = _Section("download", "// DOWNLOAD PARTS", expanded=True,
                          required=True, parent=form_wrap)
        form.addWidget(sec_dl)
        self._field_urls = _UrlListEditor(parent=form_wrap, show_caption=False)
        self._field_urls.changed.connect(self._on_anything_changed)
        sec_dl.add(self._field_urls)
        self._err_urls = self._mk_error()
        sec_dl.add(self._err_urls)

        # § ADVANCED
        sec_adv = _Section("advanced", "// ADVANCED", expanded=False, parent=form_wrap)
        form.addWidget(sec_adv)
        self._field_delete_before = QPlainTextEdit(form_wrap)
        self._field_delete_before.setObjectName("MgrTextArea")
        self._field_delete_before.setFixedHeight(62)
        self._field_delete_before.setPlaceholderText("Mỗi dòng 1 đường dẫn cần xoá")
        self._field_delete_before.textChanged.connect(self._on_anything_changed)
        sec_adv.add(_labeled(form_wrap, "DELETE BEFORE EXTRACT", self._field_delete_before,
                             hint="Mỗi dòng = một path tương đối, xoá trước khi giải nén."))

        form.addStretch(1)
        scroll.setWidget(form_wrap)
        root.addWidget(scroll, 1)

        # Footer
        btns = QDialogButtonBox(self)
        btns.setObjectName("MgrDialogBtns")
        self._cancel = btns.addButton("✕  HUỶ", QDialogButtonBox.ButtonRole.RejectRole)
        self._cancel.setObjectName("MgrSecondaryBtn")
        self._cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        self._save = btns.addButton(
            "✓  LƯU MOD" if self._editing_existing else "+  TẠO MOD",
            QDialogButtonBox.ButtonRole.AcceptRole,
        )
        self._save.setObjectName("MgrPushBtn")
        self._save.setCursor(Qt.CursorShape.PointingHandCursor)
        btns.accepted.connect(self._on_save)
        btns.rejected.connect(self._on_cancel)
        root.addWidget(btns)

        # Populate combo + form
        self._populate_game_combo()
        if self._editing_existing:
            self._populate_form(existing or {}, gid or "")
        else:
            self._populate_form_blank(default_group)
        self._dirty = False
        self._update_hero()

        # Esc handling via QDialog default; intercept reject to confirm if dirty
        QShortcut(QKeySequence("Ctrl+Return"), self,
                  activated=self._on_save).setContext(
            Qt.ShortcutContext.WidgetWithChildrenShortcut)

    def reject(self) -> None:  # noqa: D401
        self._on_cancel()

    # ── Field helpers ───────────────────────────────────────────────

    def _mk_input(self, placeholder: str) -> QLineEdit:
        e = QLineEdit(self)
        e.setObjectName("MgrInput")
        e.setPlaceholderText(placeholder)
        e.textEdited.connect(self._on_anything_changed)
        return e

    def _mk_error(self) -> QLabel:
        lbl = QLabel("", self)
        lbl.setObjectName("MgrFieldError")
        lbl.setWordWrap(True)
        lbl.setVisible(False)
        return lbl

    def _populate_game_combo(self) -> None:
        self._field_game.blockSignals(True)
        try:
            self._field_game.clear()
            self._field_game.addItem("")
            seen: set[str] = {""}
            for k in self._theme_keys:
                k = (k or "").strip()
                if k and k not in seen:
                    self._field_game.addItem(k)
                    seen.add(k)
        finally:
            self._field_game.blockSignals(False)

    def _populate_form(self, game: dict, gid: str) -> None:
        self._field_id.setText(str(gid))
        self._field_name.setText(str(game.get("name") or ""))
        self._set_game_text(str(game.get("game") or ""))
        self._field_version.setText(str(game.get("version") or ""))
        tp = str(game.get("type") or "zip")
        idx = self._field_type.findText(tp)
        if idx >= 0:
            self._field_type.setCurrentIndex(idx)
        else:
            self._field_type.setEditText(tp)
        tag_raw = game.get("tag")
        tag_norm = str(tag_raw).strip().upper() if tag_raw else ""
        idx = self._field_tag.findData(tag_norm or None)
        self._field_tag.setCurrentIndex(idx if idx >= 0 else 0)
        self._field_password.setText(
            "" if game.get("password") is None else str(game.get("password"))
        )
        self._field_launch.setText(
            "" if game.get("launch_file") is None else str(game.get("launch_file"))
        )
        self._field_path_guide.setPlainText(str(game.get("path_guide") or ""))
        dbe = game.get("delete_before_extract") or []
        self._field_delete_before.setPlainText("\n".join(str(x) for x in dbe))
        urls = list(game.get("urls") or [])
        if not urls and game.get("url"):
            urls = [str(game["url"])]
        self._field_urls.set_values(urls)

    def _populate_form_blank(self, default_group: str) -> None:
        # Suggest next free id
        n = 1
        while str(n) in self._used_ids:
            n += 1
        self._field_id.setText(str(n))
        self._field_name.setText("")
        self._set_game_text(default_group)
        self._field_version.setText("")
        self._field_type.setCurrentIndex(0)
        self._field_tag.setCurrentIndex(0)
        self._field_password.setText("")
        self._field_launch.setText("")
        self._field_path_guide.setPlainText("")
        self._field_delete_before.setPlainText("")
        self._field_urls.set_values([])

    def _set_game_text(self, value: str) -> None:
        idx = self._field_game.findText(value)
        if idx >= 0:
            self._field_game.setCurrentIndex(idx)
        else:
            self._field_game.setEditText(value)

    def _on_anything_changed(self, *_args) -> None:
        self._dirty = True

    def _update_hero(self) -> None:
        key = self._field_game.currentText().strip()
        exists = key in self._theme_keys if key else False
        has_image = key in self._theme_image_keys if key else False
        self._hero.update_state(key, exists, has_image)

    # ── Save / cancel ───────────────────────────────────────────────

    def _on_save(self) -> None:
        if not self._validate():
            return
        self.accept()

    def _on_cancel(self) -> None:
        if self._dirty:
            ans = QMessageBox.question(
                self, "Bỏ thay đổi?",
                "Bạn có thay đổi chưa lưu. Đóng modal sẽ mất hết. Tiếp tục?",
            )
            if ans != QMessageBox.StandardButton.Yes:
                return
        QDialog.reject(self)

    def _validate(self) -> bool:
        ok = True
        first_invalid_widget: QWidget | None = None

        new_id = self._field_id.text().strip()
        if not new_id or not new_id.isdigit() or int(new_id) <= 0:
            self._err_id.setText("ID phải là số nguyên dương.")
            self._err_id.setVisible(True)
            ok = False
            first_invalid_widget = self._field_id
        elif new_id in self._used_ids:
            self._err_id.setText(f"ID '{new_id}' đã tồn tại. Chọn số khác.")
            self._err_id.setVisible(True)
            ok = False
            first_invalid_widget = self._field_id
        else:
            self._err_id.setVisible(False)

        if not self._field_name.text().strip():
            self._err_name.setText("Tên không được để trống.")
            self._err_name.setVisible(True)
            ok = False
            if first_invalid_widget is None:
                first_invalid_widget = self._field_name
        else:
            self._err_name.setVisible(False)

        if self._field_urls.count_non_empty() == 0:
            self._err_urls.setText("Cần ít nhất 1 download part.")
            self._err_urls.setVisible(True)
            ok = False
            if first_invalid_widget is None:
                first_invalid_widget = self._field_urls
        else:
            self._err_urls.setVisible(False)

        if not ok and first_invalid_widget is not None:
            first_invalid_widget.setFocus()
        return ok

    # ── Result extraction ───────────────────────────────────────────

    def result_payload(self) -> tuple[str, dict]:
        """Returns (new_id, game_dict). Call only after exec() == Accepted."""
        new_id = self._field_id.text().strip()
        urls = self._field_urls.values()
        dbe_raw = self._field_delete_before.toPlainText().splitlines()
        tag = self._field_tag.currentData()
        pwd = self._field_password.text().strip()
        launch = self._field_launch.text().strip()
        game = {
            "name": self._field_name.text().strip(),
            "game": self._field_game.currentText().strip(),
            "version": self._field_version.text().strip(),
            "type": self._field_type.currentText().strip() or "zip",
            "tag": tag or None,
            "password": pwd or None,
            "launch_file": launch or None,
            "path_guide": self._field_path_guide.toPlainText().strip(),
            "delete_before_extract": [s.strip() for s in dbe_raw if s.strip()],
            "urls": urls,
        }
        # Preserve any other fields from the original entry
        if self._initial:
            for k, v in self._initial.items():
                if k not in game and k != "url":
                    game[k] = v
        return new_id, game


class _HeroLinkStrip(QFrame):
    """Cross-link pill: shows whether the typed `game` matches a theme."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("MgrHeroLink")
        self.setVisible(False)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(10, 8, 10, 8)
        lay.setSpacing(8)
        self._state = QLabel("", self)
        self._state.setObjectName("MgrHeroState")
        self._state.setFixedWidth(14)
        lay.addWidget(self._state)
        self._text = QLabel("", self)
        self._text.setObjectName("MgrHeroText")
        self._text.setWordWrap(True)
        lay.addWidget(self._text, 1)

    def update_state(self, key: str, exists: bool, has_image: bool) -> None:
        if not key:
            self.setVisible(False)
            return
        if exists and has_image:
            self._state.setText("✓")
            self._text.setText(
                f"Liên kết Theme <b>{key}</b> · hero image sẵn sàng."
            )
            self.setProperty("state", "ok")
        elif exists:
            self._state.setText("!")
            self._text.setText(
                f"Theme <b>{key}</b> tồn tại nhưng <u>thiếu hero image</u>."
            )
            self.setProperty("state", "warn")
        else:
            self._state.setText("?")
            self._text.setText(
                f"Chưa có Theme cho <b>{key}</b>. Tạo Theme ở tab THEMES."
            )
            self.setProperty("state", "missing")
        self.setVisible(True)
        self.style().unpolish(self)
        self.style().polish(self)


# ════════════════════════════════════════════════════════════════════
# Modal: theme editor
# ════════════════════════════════════════════════════════════════════

class _ThemeEditDialog(QDialog):
    """Modal for creating / editing a theme entry."""

    def __init__(
        self,
        *,
        key: str | None,
        existing: dict | None,
        used_keys: set[str],
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("MgrEditDialog")
        self.setModal(True)
        self.setMinimumSize(640, 600)

        self._editing = existing is not None
        self._original_key = key
        self._used_keys = set(used_keys)
        if self._editing and key:
            self._used_keys.discard(key)
        self._dirty = False
        self._initial = copy.deepcopy(existing) if existing else None

        root = QVBoxLayout(self)
        root.setContentsMargins(24, 22, 24, 18)
        root.setSpacing(14)

        title = QLabel("// SỬA THEME" if self._editing else "// THEME MỚI", self)
        title.setObjectName("MgrDialogTitle")
        root.addWidget(title)
        subtitle = QLabel(
            f"Key: {key}" if self._editing else "Tạo theme cho một game.",
            self,
        )
        subtitle.setObjectName("MgrDialogSubtitle")
        root.addWidget(subtitle)

        scroll = QScrollArea(self)
        scroll.setObjectName("MgrDialogScroll")
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        form_wrap = QWidget()
        form_wrap.setObjectName("MgrFormWrap")
        form = QVBoxLayout(form_wrap)
        form.setContentsMargins(2, 2, 18, 18)
        form.setSpacing(10)

        # Hero preview (live)
        self._hero_preview = QLabel(form_wrap)
        self._hero_preview.setObjectName("MgrThemeThumb")
        self._hero_preview.setFixedHeight(_THUMB_H + 20)
        self._hero_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._hero_preview.setText("NO IMAGE")
        form.addWidget(self._hero_preview)

        sec_id = _Section("theme-id", "// IDENTITY", expanded=True, parent=form_wrap)
        form.addWidget(sec_id)
        self._field_key = QLineEdit(form_wrap)
        self._field_key.setObjectName("MgrInput")
        self._field_key.setPlaceholderText("vd: Elden Ring Nightreign")
        self._field_key.textEdited.connect(self._on_anything_changed)
        self._err_key = self._mk_error()
        sec_id.add(_labeled(form_wrap, "KEY *", self._field_key,
                            hint="Khớp với field 'game' trong các Mod.",
                            error=self._err_key))

        sec_media = _Section("theme-media", "// MEDIA", expanded=True, parent=form_wrap)
        form.addWidget(sec_media)
        self._field_image = QLineEdit(form_wrap)
        self._field_image.setObjectName("MgrInput")
        self._field_image.setPlaceholderText("https://... (hero image)")
        self._field_image.textEdited.connect(self._on_image_changed)
        sec_media.add(_labeled(form_wrap, "HERO IMAGE", self._field_image))

        self._field_trailer = QLineEdit(form_wrap)
        self._field_trailer.setObjectName("MgrInput")
        self._field_trailer.setPlaceholderText("https://youtube.com/...")
        self._field_trailer.textEdited.connect(self._on_anything_changed)
        sec_media.add(_labeled(form_wrap, "TRAILER URL", self._field_trailer))

        sec_slide = _Section("theme-slideshow", "// SLIDESHOW", expanded=True, parent=form_wrap)
        form.addWidget(sec_slide)
        self._field_slideshow = _UrlListEditor(parent=form_wrap, show_caption=False)
        self._field_slideshow.changed.connect(self._on_anything_changed)
        sec_slide.add(self._field_slideshow)

        form.addStretch(1)
        scroll.setWidget(form_wrap)
        root.addWidget(scroll, 1)

        btns = QDialogButtonBox(self)
        btns.setObjectName("MgrDialogBtns")
        self._cancel = btns.addButton("✕  HUỶ", QDialogButtonBox.ButtonRole.RejectRole)
        self._cancel.setObjectName("MgrSecondaryBtn")
        self._cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        self._save = btns.addButton(
            "✓  LƯU THEME" if self._editing else "+  TẠO THEME",
            QDialogButtonBox.ButtonRole.AcceptRole,
        )
        self._save.setObjectName("MgrPushBtn")
        self._save.setCursor(Qt.CursorShape.PointingHandCursor)
        btns.accepted.connect(self._on_save)
        btns.rejected.connect(self._on_cancel)
        root.addWidget(btns)

        if self._editing:
            self._populate_form(existing or {}, key or "")
        else:
            self._field_key.setText("")

        # Live thumbnail load
        self._image_debounce = QTimer(self)
        self._image_debounce.setSingleShot(True)
        self._image_debounce.setInterval(450)
        self._image_debounce.timeout.connect(self._reload_thumb)
        if self._editing:
            self._reload_thumb()

    def reject(self) -> None:
        self._on_cancel()

    def _mk_error(self) -> QLabel:
        lbl = QLabel("", self)
        lbl.setObjectName("MgrFieldError")
        lbl.setWordWrap(True)
        lbl.setVisible(False)
        return lbl

    def _populate_form(self, theme: dict, key: str) -> None:
        self._field_key.setText(key)
        self._field_image.setText(str(theme.get("image") or ""))
        self._field_trailer.setText(str(theme.get("trailer_url") or ""))
        self._field_slideshow.set_values(
            [str(x) for x in (theme.get("slideshow") or [])]
        )

    def _on_anything_changed(self, *_a) -> None:
        self._dirty = True

    def _on_image_changed(self, *_a) -> None:
        self._dirty = True
        self._image_debounce.start()

    def _reload_thumb(self) -> None:
        url = self._field_image.text().strip()
        if not url:
            self._hero_preview.setText("NO IMAGE")
            self._hero_preview.setPixmap(QPixmap())
            return
        self._hero_preview.setText("LOADING...")
        self._hero_preview.setPixmap(QPixmap())
        _ThumbnailLoader.instance().request(url, self._apply_thumb)

    def _apply_thumb(self, pixmap: QPixmap | None) -> None:
        try:
            if pixmap is None or pixmap.isNull():
                self._hero_preview.setText("KHÔNG TẢI ĐƯỢC ẢNH")
                self._hero_preview.setPixmap(QPixmap())
                return
            scaled = pixmap.scaled(
                self._hero_preview.width() or _THUMB_W, _THUMB_H + 20,
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation,
            )
            self._hero_preview.setPixmap(scaled)
            self._hero_preview.setText("")
        except RuntimeError:
            # Dialog closed before reply landed.
            pass

    def _on_save(self) -> None:
        if not self._validate():
            return
        self.accept()

    def _on_cancel(self) -> None:
        if self._dirty:
            ans = QMessageBox.question(
                self, "Bỏ thay đổi?",
                "Bạn có thay đổi chưa lưu. Đóng modal sẽ mất hết. Tiếp tục?",
            )
            if ans != QMessageBox.StandardButton.Yes:
                return
        QDialog.reject(self)

    def _validate(self) -> bool:
        ok = True
        key = self._field_key.text().strip()
        if not key:
            self._err_key.setText("Key không được để trống.")
            self._err_key.setVisible(True)
            self._field_key.setFocus()
            ok = False
        elif key in self._used_keys:
            self._err_key.setText(f"Key '{key}' đã tồn tại.")
            self._err_key.setVisible(True)
            self._field_key.setFocus()
            ok = False
        else:
            self._err_key.setVisible(False)
        return ok

    def result_payload(self) -> tuple[str, dict]:
        return self._field_key.text().strip(), {
            "image": self._field_image.text().strip(),
            "slideshow": self._field_slideshow.values(),
            "trailer_url": self._field_trailer.text().strip(),
        }


# ════════════════════════════════════════════════════════════════════
# Push preview dialog
# ════════════════════════════════════════════════════════════════════

class _PushPreviewDialog(QDialog):
    def __init__(self, summary: dict[str, list[str]],
                 default_message: str, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("MgrPushDialog")
        self.setWindowTitle("Đẩy cấu hình lên Server")
        self.setModal(True)
        self.setMinimumSize(560, 460)

        root = QVBoxLayout(self)
        root.setContentsMargins(24, 22, 24, 18)
        root.setSpacing(14)

        title = QLabel("// XÁC NHẬN ĐẨY", self)
        title.setObjectName("MgrDialogTitle")
        root.addWidget(title)

        subtitle = QLabel(
            "Kiểm tra những gì sẽ được đẩy lên Server. Hành động này không thể hoàn tác.",
            self,
        )
        subtitle.setObjectName("MgrDialogSubtitle")
        subtitle.setWordWrap(True)
        root.addWidget(subtitle)

        stats = QHBoxLayout()
        stats.setSpacing(8)
        for key, label in (("added", "THÊM"), ("modified", "SỬA"), ("deleted", "XOÁ")):
            count = len(summary.get(key, []))
            chip = QLabel(f"{label} · {count}", self)
            chip.setObjectName("MgrPushStat")
            chip.setProperty("kind", key)
            chip.setProperty("empty", "true" if count == 0 else "false")
            stats.addWidget(chip)
        stats.addStretch(1)
        root.addLayout(stats)

        scroll = QScrollArea(self)
        scroll.setObjectName("MgrPushScroll")
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        body = QWidget()
        body.setObjectName("MgrPushBody")
        body_lay = QVBoxLayout(body)
        body_lay.setContentsMargins(0, 0, 0, 0)
        body_lay.setSpacing(10)

        for kind, caption in (
            ("added", "// MỚI"),
            ("modified", "// THAY ĐỔI"),
            ("deleted", "// ĐÃ XOÁ"),
        ):
            items = summary.get(kind, [])
            if not items:
                continue
            heading = QLabel(f"{caption}  ({len(items)})", body)
            heading.setObjectName("MgrPushGroup")
            body_lay.addWidget(heading)
            for entry in items:
                row = QLabel(f"  • {entry}", body)
                row.setObjectName("MgrPushItem")
                row.setProperty("kind", kind)
                row.setWordWrap(True)
                body_lay.addWidget(row)

        if not any(summary.get(k) for k in ("added", "modified", "deleted")):
            empty = QLabel("Không có thay đổi để đẩy.", body)
            empty.setObjectName("MgrPushEmpty")
            body_lay.addWidget(empty)

        body_lay.addStretch(1)
        scroll.setWidget(body)
        root.addWidget(scroll, 1)

        msg_label = QLabel("GHI CHÚ THAY ĐỔI", self)
        msg_label.setObjectName("MgrFieldLabel")
        root.addWidget(msg_label)
        self._msg_edit = QLineEdit(default_message, self)
        self._msg_edit.setObjectName("MgrInput")
        self._msg_edit.setPlaceholderText("vd: chore: update mod table")
        root.addWidget(self._msg_edit)

        btns = QDialogButtonBox(self)
        cancel = btns.addButton("✕  HUỶ", QDialogButtonBox.ButtonRole.RejectRole)
        cancel.setObjectName("MgrSecondaryBtn")
        cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        confirm = btns.addButton("⇡  ĐẨY LÊN SERVER",
                                 QDialogButtonBox.ButtonRole.AcceptRole)
        confirm.setObjectName("MgrPushBtn")
        confirm.setCursor(Qt.CursorShape.PointingHandCursor)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        root.addWidget(btns)

    def message(self) -> str:
        return self._msg_edit.text().strip()


# ════════════════════════════════════════════════════════════════════
# Games browser (cards grouped by `game` field)
# ════════════════════════════════════════════════════════════════════

class _GamesBrowser(QWidget):
    changed = pyqtSignal()
    request_open_theme = pyqtSignal(str)

    def __init__(self, manager: "ManagerView", parent=None) -> None:
        super().__init__(parent)
        self._manager = manager
        self._games: dict[str, dict] = {}
        self._baseline: dict[str, dict] = {}
        self._order: list[str] = []
        self._groups: dict[str, list[str]] = {}
        self._cards: dict[str, _GameCard] = {}
        self._bands: dict[str, _GroupBand] = {}
        self._collapsed: set[str] = self._load_collapsed()
        self._filter = "all"
        self._search = ""
        self._theme_keys: list[str] = []
        self._theme_image_keys: set[str] = set()
        self._pending_delete: dict | None = None
        self._focused_group: str = ""

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.addWidget(self._build_toolbar())
        root.addWidget(self._build_body(), 1)
        root.addWidget(self.undo_ribbon)

    # ── Toolbar ─────────────────────────────────────────────────────

    def _build_toolbar(self) -> QWidget:
        bar = QFrame(self)
        bar.setObjectName("MgrToolbar")
        lay = QHBoxLayout(bar)
        lay.setContentsMargins(0, 0, 0, 10)
        lay.setSpacing(10)
        self._search_bar = _SearchBar("Tìm mod (tên / id / game / tag)...", bar)
        self._search_bar.text_changed.connect(self._on_search)
        lay.addWidget(self._search_bar, 1)
        self._filters = _FilterChips(bar)
        self._filters.filter_changed.connect(self._on_filter)
        lay.addWidget(self._filters)
        self._add_btn = QPushButton("+ MOD MỚI", bar)
        self._add_btn.setObjectName("MgrPushBtn")
        self._add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._add_btn.clicked.connect(self._on_add)
        lay.addWidget(self._add_btn)
        return bar

    def _build_body(self) -> QWidget:
        self._scroll = QScrollArea(self)
        self._scroll.setObjectName("MgrCardScroll")
        self._scroll.setWidgetResizable(True)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        body = QWidget()
        body.setObjectName("MgrCardBody")
        self._body_lay = QVBoxLayout(body)
        self._body_lay.setContentsMargins(0, 0, 0, 0)
        self._body_lay.setSpacing(10)
        self._empty = QLabel("Không có mod nào.", body)
        self._empty.setObjectName("MgrEmptyState")
        self._empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._empty.setVisible(False)
        self._body_lay.addWidget(self._empty)
        self._body_lay.addStretch(1)
        self._scroll.setWidget(body)
        self.undo_ribbon = _UndoRibbon(self)
        self.undo_ribbon.undo_clicked.connect(self._on_undo_delete)
        self.undo_ribbon.dismissed.connect(lambda: setattr(self, "_pending_delete", None))
        return self._scroll

    # ── State management ────────────────────────────────────────────

    def load(self, games_raw: dict) -> None:
        self._games = {}
        self._order = []
        for key, value in games_raw.items():
            if key in _RESERVED_GAME_KEYS or not isinstance(value, dict):
                continue
            self._games[str(key)] = dict(value)
            self._order.append(str(key))
        self._baseline = copy.deepcopy(self._games)
        self._rebuild()

    def dump_into(self, games_raw: dict) -> None:
        for key in list(games_raw.keys()):
            if key not in _RESERVED_GAME_KEYS:
                del games_raw[key]
        for gid in self._order:
            games_raw[gid] = self._games[gid]

    def diff_summary(self) -> dict[str, list[str]]:
        added, modified = [], []
        for gid in self._order:
            label = self._games[gid].get("name") or gid
            entry = f"#{gid} · {label}"
            if gid not in self._baseline:
                added.append(entry)
            elif self._games[gid] != self._baseline[gid]:
                modified.append(entry)
        deleted = []
        for gid, snapshot in self._baseline.items():
            if gid not in self._games:
                deleted.append(f"#{gid} · {snapshot.get('name') or gid}")
        return {"added": added, "modified": modified, "deleted": deleted}

    def is_dirty_gid(self, gid: str) -> bool:
        base = self._baseline.get(gid)
        cur = self._games.get(gid)
        if (base is None) != (cur is None):
            return True
        return base != cur

    def dirty_count(self) -> int:
        n = sum(1 for gid in self._order if self.is_dirty_gid(gid))
        n += sum(1 for gid in self._baseline if gid not in self._games)
        return n

    def mark_clean(self) -> None:
        self._baseline = copy.deepcopy(self._games)
        for card in self._cards.values():
            card.update_state(self._games.get(card._gid) or {}, False)
        for key, band in self._bands.items():
            band.set_dirty_count(0)

    def set_theme_keys(self, keys: list[str], image_keys: set[str]) -> None:
        self._theme_keys = list(keys)
        self._theme_image_keys = set(image_keys)

    def used_ids(self) -> set[str]:
        return set(self._games.keys())

    def games(self) -> dict[str, dict]:
        return self._games

    def rename_game_key(self, old_key: str, new_key: str) -> int:
        old_key = (old_key or "").strip()
        new_key = (new_key or "").strip()
        if not old_key or old_key == new_key:
            return 0
        n = 0
        for gid in self._order:
            if (self._games[gid].get("game") or "").strip() == old_key:
                self._games[gid]["game"] = new_key
                n += 1
        if n:
            self._rebuild()
            self.changed.emit()
        return n

    # ── Rebuild card layout ─────────────────────────────────────────

    def _rebuild(self) -> None:
        # Clear previous bands
        for band in self._bands.values():
            band.deleteLater()
        self._bands.clear()
        self._cards.clear()
        # Remove all items except the trailing stretch + empty label
        while self._body_lay.count() > 2:
            item = self._body_lay.takeAt(0)
            w = item.widget()
            if w is not None and w not in (self._empty,):
                w.deleteLater()

        # Build groups
        self._groups = {}
        for gid in self._order:
            key = (self._games[gid].get("game") or "").strip()
            self._groups.setdefault(key, []).append(gid)
        ordered_keys = [k for k in self._groups if k != ""]
        if "" in self._groups:
            ordered_keys.append("")

        insert_idx = 0
        for key in ordered_keys:
            gids = self._groups[key]
            label = key.upper() if key else "(CHƯA NHÓM)"
            expanded = key not in self._collapsed
            dirty_n = sum(1 for g in gids if self.is_dirty_gid(g))
            band = _GroupBand(key, label, len(gids), dirty_n, expanded, self)
            band.toggle_requested.connect(self._on_group_toggle)
            band.add_requested.connect(self._on_group_add)
            band.menu_requested.connect(self._on_group_menu)
            body_lay: QVBoxLayout = band.body_layout()
            for gid in gids:
                card = _GameCard(gid, self._games[gid], self.is_dirty_gid(gid), band)
                card.edit_requested.connect(self._open_edit_modal)
                card.menu_requested.connect(self._on_card_menu)
                body_lay.addWidget(card)
                self._cards[gid] = card
            self._body_lay.insertWidget(insert_idx, band)
            self._bands[key] = band
            insert_idx += 1

        self._apply_filter()

    def _refresh_card(self, gid: str) -> None:
        card = self._cards.get(gid)
        if card is None:
            return
        card.update_state(self._games.get(gid) or {}, self.is_dirty_gid(gid))

    def _refresh_band_count(self, key: str) -> None:
        gids = self._groups.get(key, [])
        band = self._bands.get(key)
        if band is None:
            return
        band.set_count(len(gids))
        band.set_dirty_count(sum(1 for g in gids if self.is_dirty_gid(g)))

    # ── Filter / search ─────────────────────────────────────────────

    def _on_search(self, query: str) -> None:
        self._search = query.lower()
        self._apply_filter()

    def _on_filter(self, key: str) -> None:
        self._filter = key
        self._apply_filter()

    def _apply_filter(self) -> None:
        any_visible = False
        for key, gids in self._groups.items():
            band = self._bands.get(key)
            if band is None:
                continue
            shown = 0
            for gid in gids:
                card = self._cards.get(gid)
                if card is None:
                    continue
                visible = self._matches(gid, key)
                card.setVisible(visible)
                if visible:
                    shown += 1
            show_band = shown > 0 or (
                self._filter == "all" and not self._search
            )
            band.setVisible(show_band)
            if show_band:
                any_visible = True
        self._empty.setVisible(not any_visible)

    def _matches(self, gid: str, group_key: str) -> bool:
        if self._filter == "dirty" and not self.is_dirty_gid(gid):
            return False
        if self._filter == "ungrouped" and group_key != "":
            return False
        if not self._search:
            return True
        g = self._games.get(gid) or {}
        haystack = " ".join(str(g.get(k) or "") for k in ("name", "game", "tag", "version"))
        return self._search in haystack.lower() or self._search in gid.lower()

    # ── Mod CRUD ────────────────────────────────────────────────────

    def _on_add(self) -> None:
        self._open_new_modal(default_group=self._focused_group)

    def _open_new_modal(self, *, default_group: str = "") -> None:
        dlg = _GameEditDialog(
            gid=None,
            existing=None,
            theme_keys=self._theme_keys,
            theme_image_keys=self._theme_image_keys,
            used_ids=self.used_ids(),
            default_group=default_group,
            parent=self.window(),
        )
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        new_id, payload = dlg.result_payload()
        self._games[new_id] = payload
        self._order.append(new_id)
        self._collapsed.discard((payload.get("game") or "").strip())
        self._save_collapsed()
        self._rebuild()
        self.changed.emit()

    def _open_edit_modal(self, gid: str) -> None:
        existing = self._games.get(gid)
        if existing is None:
            return
        dlg = _GameEditDialog(
            gid=gid,
            existing=existing,
            theme_keys=self._theme_keys,
            theme_image_keys=self._theme_image_keys,
            used_ids=self.used_ids(),
            default_group=(existing.get("game") or "").strip(),
            parent=self.window(),
        )
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        new_id, payload = dlg.result_payload()
        # Apply ID change if any
        if new_id != gid:
            self._games[new_id] = payload
            self._order[self._order.index(gid)] = new_id
            if gid in self._baseline:
                self._baseline[new_id] = self._baseline.pop(gid)
            del self._games[gid]
        else:
            self._games[gid] = payload
        self._rebuild()
        self.changed.emit()

    def _delete_gid(self, gid: str) -> None:
        if gid not in self._games:
            return
        snapshot = copy.deepcopy(self._games[gid])
        idx = self._order.index(gid)
        self._pending_delete = {"gid": gid, "snapshot": snapshot, "idx": idx}
        del self._games[gid]
        self._order.remove(gid)
        self._rebuild()
        self.undo_ribbon.show_for(
            f"Đã xoá '{snapshot.get('name') or gid}' (#{gid})"
        )
        self.changed.emit()

    def _on_undo_delete(self) -> None:
        pending = self._pending_delete
        if not pending:
            return
        self._pending_delete = None
        gid = pending["gid"]
        idx = min(pending["idx"], len(self._order))
        self._games[gid] = pending["snapshot"]
        self._order.insert(idx, gid)
        self._rebuild()
        self.changed.emit()

    def _duplicate_gid(self, gid: str) -> None:
        src = self._games.get(gid)
        if src is None:
            return
        used = {int(g) for g in self._games if g.isdigit()}
        n = 1
        while n in used:
            n += 1
        new_id = str(n)
        payload = copy.deepcopy(src)
        payload["name"] = f"{src.get('name') or 'Mod'} (sao chép)"
        self._games[new_id] = payload
        self._order.append(new_id)
        self._rebuild()
        self.changed.emit()

    def _on_card_menu(self, gid: str, pos: QPoint) -> None:
        menu = QMenu(self)
        menu.addAction("✎  Sửa…", lambda: self._open_edit_modal(gid))
        menu.addAction("⊕  Nhân bản", lambda: self._duplicate_gid(gid))
        menu.addSeparator()
        menu.addAction("✕  Xoá", lambda: self._delete_gid(gid))
        menu.exec(pos)

    # ── Group operations ────────────────────────────────────────────

    def _on_group_toggle(self, key: str) -> None:
        band = self._bands.get(key)
        if band is None:
            return
        expanded = key in self._collapsed
        band.set_expanded(expanded)
        if expanded:
            self._collapsed.discard(key)
        else:
            self._collapsed.add(key)
        self._focused_group = key
        self._save_collapsed()

    def _on_group_add(self, key: str) -> None:
        self._focused_group = key
        self._open_new_modal(default_group=key)

    def _on_group_menu(self, key: str, pos: QPoint) -> None:
        menu = QMenu(self)
        menu.addAction("✎  Đổi tên nhóm…", lambda: self._rename_group(key))
        menu.addAction("+  Thêm mod vào nhóm", lambda: self._on_group_add(key))
        menu.addSeparator()
        menu.addAction("▸  Thu gọn nhóm khác", lambda: self._collapse_others(key))
        if key:
            menu.addAction("→  Mở Theme tương ứng",
                           lambda: self.request_open_theme.emit(key))
        menu.exec(pos)

    def _rename_group(self, key: str) -> None:
        new_key, ok = QInputDialog.getText(
            self, "Đổi tên nhóm",
            "Tên nhóm mới (ghi vào trường `game` của mọi mod trong nhóm):",
            QLineEdit.EchoMode.Normal, key,
        )
        if not ok:
            return
        new_key = (new_key or "").strip()
        if new_key == key:
            return
        for gid in self._groups.get(key, []):
            self._games[gid]["game"] = new_key
        if key in self._collapsed:
            self._collapsed.discard(key)
            if new_key:
                self._collapsed.add(new_key)
            self._save_collapsed()
        self._focused_group = new_key
        self._rebuild()
        self.changed.emit()

    def _collapse_others(self, key: str) -> None:
        for k, band in self._bands.items():
            if k == key:
                band.set_expanded(True)
                self._collapsed.discard(k)
            else:
                band.set_expanded(False)
                self._collapsed.add(k)
        self._save_collapsed()

    # ── Persistence ─────────────────────────────────────────────────

    def _load_collapsed(self) -> set[str]:
        data = _read_json(_ui_state_path())
        return {str(x) for x in data.get("collapsed", []) if isinstance(x, str)}

    def _save_collapsed(self) -> None:
        data = _read_json(_ui_state_path())
        data["collapsed"] = sorted(self._collapsed)
        try:
            p = _ui_state_path()
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        except Exception:
            log.exception("Save collapsed state failed")

    # ── Public helpers ──────────────────────────────────────────────

    def focus_search(self) -> None:
        self._search_bar.focus_input()


# ════════════════════════════════════════════════════════════════════
# Themes browser
# ════════════════════════════════════════════════════════════════════

class _ThemesBrowser(QWidget):
    changed = pyqtSignal()
    keys_changed = pyqtSignal()
    key_renamed = pyqtSignal(str, str)

    def __init__(self, manager: "ManagerView", parent=None) -> None:
        super().__init__(parent)
        self._manager = manager
        self._themes: dict[str, dict] = {}
        self._baseline: dict[str, dict] = {}
        self._order: list[str] = []
        self._cards: dict[str, _ThemeCard] = {}
        self._search = ""
        self._pending_delete: dict | None = None

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.addWidget(self._build_toolbar())
        root.addWidget(self._build_body(), 1)
        root.addWidget(self.undo_ribbon)

    def _build_toolbar(self) -> QWidget:
        bar = QFrame(self)
        bar.setObjectName("MgrToolbar")
        lay = QHBoxLayout(bar)
        lay.setContentsMargins(0, 0, 0, 10)
        lay.setSpacing(10)
        self._search_bar = _SearchBar("Tìm theme...", bar)
        self._search_bar.text_changed.connect(self._on_search)
        lay.addWidget(self._search_bar, 1)
        self._add_btn = QPushButton("+ THEME MỚI", bar)
        self._add_btn.setObjectName("MgrPushBtn")
        self._add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._add_btn.clicked.connect(self._on_add)
        lay.addWidget(self._add_btn)
        return bar

    def _build_body(self) -> QWidget:
        scroll = QScrollArea(self)
        scroll.setObjectName("MgrCardScroll")
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        body = QWidget()
        body.setObjectName("MgrCardBody")
        self._grid = QGridLayout(body)
        self._grid.setContentsMargins(0, 0, 0, 0)
        self._grid.setSpacing(10)
        self._grid.setColumnStretch(0, 1)
        self._grid.setColumnStretch(1, 1)
        self._empty = QLabel("Không có theme nào.", body)
        self._empty.setObjectName("MgrEmptyState")
        self._empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._empty.setVisible(False)
        # Empty goes into row 0 col 0 by default; it'll be re-placed after rebuild
        scroll.setWidget(body)
        self.undo_ribbon = _UndoRibbon(self)
        self.undo_ribbon.undo_clicked.connect(self._on_undo_delete)
        self.undo_ribbon.dismissed.connect(lambda: setattr(self, "_pending_delete", None))
        return scroll

    def load(self, themes_raw: dict) -> None:
        self._themes = {}
        self._order = []
        for key, value in themes_raw.items():
            if isinstance(value, str):
                self._themes[str(key)] = {"image": value, "slideshow": [], "trailer_url": ""}
            elif isinstance(value, dict):
                self._themes[str(key)] = {
                    "image": str(value.get("image") or ""),
                    "slideshow": [str(x) for x in (value.get("slideshow") or [])],
                    "trailer_url": str(value.get("trailer_url") or ""),
                }
            else:
                continue
            self._order.append(str(key))
        self._baseline = copy.deepcopy(self._themes)
        self._rebuild()
        self.keys_changed.emit()

    def keys(self) -> list[str]:
        return list(self._order)

    def keys_with_image(self) -> set[str]:
        return {k for k in self._order if (self._themes[k].get("image") or "").strip()}

    def dump(self) -> dict:
        out: dict[str, Any] = {}
        for key in self._order:
            t = self._themes[key]
            out[key] = {
                "image": t.get("image") or "",
                "slideshow": list(t.get("slideshow") or []),
                "trailer_url": t.get("trailer_url") or "",
            }
        return out

    def diff_summary(self) -> dict[str, list[str]]:
        added, modified = [], []
        for key in self._order:
            if key not in self._baseline:
                added.append(f"theme: {key}")
            elif self._themes[key] != self._baseline[key]:
                modified.append(f"theme: {key}")
        deleted = [f"theme: {k}" for k in self._baseline if k not in self._themes]
        return {"added": added, "modified": modified, "deleted": deleted}

    def is_dirty_key(self, key: str) -> bool:
        return self._baseline.get(key) != self._themes.get(key)

    def dirty_count(self) -> int:
        n = sum(1 for k in self._order if self.is_dirty_key(k))
        n += sum(1 for k in self._baseline if k not in self._themes)
        return n

    def mark_clean(self) -> None:
        self._baseline = copy.deepcopy(self._themes)
        self._rebuild()

    def mod_count_by_key(self) -> dict[str, int]:
        counts: dict[str, int] = {k: 0 for k in self._order}
        games = self._manager.games_editor.games()
        for g in games.values():
            key = (g.get("game") or "").strip()
            if key in counts:
                counts[key] += 1
        return counts

    def _rebuild(self) -> None:
        # Clear grid
        while self._grid.count():
            item = self._grid.takeAt(0)
            w = item.widget()
            if w is not None and w is not self._empty:
                w.deleteLater()
        self._cards.clear()

        counts = self.mod_count_by_key()
        cols = 2
        row = 0
        col = 0
        visible_count = 0
        for key in self._order:
            if self._search and self._search not in key.lower():
                continue
            theme = self._themes[key]
            card = _ThemeCard(key, theme, self.is_dirty_key(key),
                              counts.get(key, 0), self)
            card.edit_requested.connect(self._open_edit_modal)
            card.menu_requested.connect(self._on_card_menu)
            self._grid.addWidget(card, row, col)
            card.load_thumb(theme.get("image") or "")
            self._cards[key] = card
            col += 1
            if col >= cols:
                col = 0
                row += 1
            visible_count += 1
        if visible_count == 0:
            self._grid.addWidget(self._empty, 0, 0, 1, cols)
            self._empty.setVisible(True)
        else:
            self._empty.setVisible(False)

    def _on_search(self, text: str) -> None:
        self._search = text.lower()
        self._rebuild()

    def used_keys(self) -> set[str]:
        return set(self._themes.keys())

    def _on_add(self) -> None:
        dlg = _ThemeEditDialog(
            key=None, existing=None,
            used_keys=self.used_keys(),
            parent=self.window(),
        )
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        key, payload = dlg.result_payload()
        if not key:
            return
        self._themes[key] = payload
        self._order.append(key)
        self._rebuild()
        self.changed.emit()
        self.keys_changed.emit()

    def _open_edit_modal(self, key: str) -> None:
        existing = self._themes.get(key)
        if existing is None:
            return
        dlg = _ThemeEditDialog(
            key=key, existing=existing,
            used_keys=self.used_keys(),
            parent=self.window(),
        )
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        new_key, payload = dlg.result_payload()
        if not new_key:
            return
        if new_key != key:
            self._themes[new_key] = payload
            i = self._order.index(key)
            self._order[i] = new_key
            if key in self._baseline:
                self._baseline[new_key] = self._baseline.pop(key)
            del self._themes[key]
            self.key_renamed.emit(key, new_key)
        else:
            self._themes[key] = payload
        self._rebuild()
        self.changed.emit()
        self.keys_changed.emit()

    def _delete_key(self, key: str) -> None:
        if key not in self._themes:
            return
        idx = self._order.index(key)
        self._pending_delete = {
            "key": key,
            "snapshot": copy.deepcopy(self._themes[key]),
            "idx": idx,
        }
        del self._themes[key]
        self._order.remove(key)
        self._rebuild()
        self.undo_ribbon.show_for(f"Đã xoá theme '{key}'")
        self.changed.emit()
        self.keys_changed.emit()

    def _on_undo_delete(self) -> None:
        pending = self._pending_delete
        if not pending:
            return
        self._pending_delete = None
        key = pending["key"]
        idx = min(pending["idx"], len(self._order))
        self._themes[key] = pending["snapshot"]
        self._order.insert(idx, key)
        self._rebuild()
        self.changed.emit()
        self.keys_changed.emit()

    def _on_card_menu(self, key: str, pos: QPoint) -> None:
        menu = QMenu(self)
        menu.addAction("✎  Sửa…", lambda: self._open_edit_modal(key))
        menu.addSeparator()
        menu.addAction("✕  Xoá", lambda: self._delete_key(key))
        menu.exec(pos)

    def focus_search(self) -> None:
        self._search_bar.focus_input()

    def focus_key(self, key: str) -> bool:
        card = self._cards.get(key)
        if card is None:
            return False
        # Best-effort scroll
        self.parentWidget().setFocus()
        return True

    def add_stub(self, key: str) -> None:
        if key in self._themes:
            return
        self._themes[key] = {"image": "", "slideshow": [], "trailer_url": ""}
        self._order.append(key)
        self._rebuild()
        self.changed.emit()
        self.keys_changed.emit()


# ════════════════════════════════════════════════════════════════════
# Top-level Manager view
# ════════════════════════════════════════════════════════════════════

class ManagerView(QWidget):
    """Tab 3 — card grid + modal editors + server push."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("MgrView")

        self._games_raw: dict = {}
        self._themes_raw: dict = {}
        self._pushing = False
        self._loading = False
        self._push_worker: PushConfigWorker | None = None
        self._load_worker: _ConfigLoadWorker | None = None
        self._loading_dlg: LoadingDialog | None = None
        self._draft_armed = False

        outer = QVBoxLayout(self)
        outer.setContentsMargins(20, 14, 20, 14)
        outer.setSpacing(0)

        outer.addWidget(self._build_header())
        outer.addWidget(self._build_tab_strip())

        self._stack = QStackedWidget(self)
        self.games_editor = _GamesBrowser(self, self._stack)
        self.themes_editor = _ThemesBrowser(self, self._stack)
        self._stack.addWidget(self.games_editor)
        self._stack.addWidget(self.themes_editor)
        outer.addWidget(self._stack, 1)

        self.games_editor.changed.connect(self._on_any_change)
        self.themes_editor.changed.connect(self._on_any_change)
        self.themes_editor.keys_changed.connect(self._sync_game_choices)
        self.themes_editor.key_renamed.connect(self._on_theme_key_renamed)
        self.games_editor.request_open_theme.connect(self._on_open_theme_key)

        self._autosave_timer = QTimer(self)
        self._autosave_timer.setSingleShot(True)
        self._autosave_timer.setInterval(_AUTOSAVE_DEBOUNCE_MS)
        self._autosave_timer.timeout.connect(self._write_draft)

        self._install_shortcuts()
        QTimer.singleShot(0, lambda: self._reload(prefer_remote=True, check_draft=True))

    # ── Shortcuts ───────────────────────────────────────────────────

    def _install_shortcuts(self) -> None:
        ctx = Qt.ShortcutContext.WidgetWithChildrenShortcut
        for seq, slot in (
            ("Ctrl+F", self._focus_current_search),
            ("Ctrl+S", self._on_push_clicked),
            ("Ctrl+R", self._on_reload_clicked),
            ("F2", self._toggle_tab),
            ("Ctrl+N", self._shortcut_new),
        ):
            sc = QShortcut(QKeySequence(seq), self)
            sc.setContext(ctx)
            sc.activated.connect(slot)

    def _focus_current_search(self) -> None:
        if self._stack.currentIndex() == 0:
            self.games_editor.focus_search()
        else:
            self.themes_editor.focus_search()

    def _shortcut_new(self) -> None:
        if self._stack.currentIndex() == 0:
            self.games_editor._on_add()
        else:
            self.themes_editor._on_add()

    def _toggle_tab(self) -> None:
        idx = self._stack.currentIndex()
        new_idx = 1 - idx
        self._stack.setCurrentIndex(new_idx)
        self._tab_games.setChecked(new_idx == 0)
        self._tab_themes.setChecked(new_idx == 1)

    # ── Cross-tab plumbing ──────────────────────────────────────────

    def _sync_game_choices(self) -> None:
        self.games_editor.set_theme_keys(
            self.themes_editor.keys(),
            self.themes_editor.keys_with_image(),
        )
        # Re-render to update theme-name labels / counts indirectly
        # (mod count badges on theme cards depend on games state)
        self.themes_editor._rebuild()

    def _on_theme_key_renamed(self, old_key: str, new_key: str) -> None:
        affected = sum(
            1 for g in self.games_editor.games().values()
            if (g.get("game") or "").strip() == old_key
        )
        if affected == 0:
            return
        ans = QMessageBox.question(
            self, "Cascade đổi key Theme?",
            f"Có {affected} mod đang trỏ tới '{old_key}'.\n"
            f"Cập nhật tất cả sang '{new_key}'?",
        )
        if ans == QMessageBox.StandardButton.Yes:
            self.games_editor.rename_game_key(old_key, new_key)

    def _on_open_theme_key(self, key: str) -> None:
        self._stack.setCurrentIndex(1)
        self._tab_games.setChecked(False)
        self._tab_themes.setChecked(True)
        if not self.themes_editor.focus_key(key):
            ans = QMessageBox.question(
                self, "Tạo Theme mới?",
                f"Chưa có Theme cho '{key}'. Tạo stub mới?",
            )
            if ans == QMessageBox.StandardButton.Yes:
                self.themes_editor.add_stub(key)

    # ── Header / tabs ───────────────────────────────────────────────

    def _build_header(self) -> QWidget:
        frame = QFrame(self)
        frame.setObjectName("MgrHeader")
        lay = QHBoxLayout(frame)
        lay.setContentsMargins(0, 0, 0, 14)
        lay.setSpacing(10)

        title = QLabel("// CONFIG MANAGER", frame)
        title.setObjectName("MgrTitle")
        lay.addWidget(title)

        sub = QLabel("· đồng bộ với Server", frame)
        sub.setObjectName("MgrSubtitle")
        lay.addWidget(sub)

        kbd = QLabel("Ctrl+F tìm · Ctrl+S đẩy · Ctrl+N mới · F2 đổi tab", frame)
        kbd.setObjectName("MgrKbdHint")
        lay.addWidget(kbd)

        lay.addStretch(1)

        self._dirty_count_chip = QLabel("0 thay đổi", frame)
        self._dirty_count_chip.setObjectName("MgrDirtyCountChip")
        self._dirty_count_chip.setVisible(False)
        lay.addWidget(self._dirty_count_chip)

        self._status_chip = QLabel("● ĐÃ ĐỒNG BỘ", frame)
        self._status_chip.setObjectName("MgrStatusChip")
        self._status_chip.setProperty("state", "clean")
        lay.addWidget(self._status_chip)

        self._reload_btn = QPushButton("↻ TẢI LẠI", frame)
        self._reload_btn.setObjectName("MgrSecondaryBtn")
        self._reload_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._reload_btn.clicked.connect(self._on_reload_clicked)
        lay.addWidget(self._reload_btn)

        self._push_btn = QPushButton("⇡ ĐẨY LÊN SERVER", frame)
        self._push_btn.setObjectName("MgrPushBtn")
        self._push_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._push_btn.clicked.connect(self._on_push_clicked)
        self._push_btn.setEnabled(False)
        lay.addWidget(self._push_btn)
        return frame

    def _build_tab_strip(self) -> QWidget:
        frame = QFrame(self)
        frame.setObjectName("MgrTabStrip")
        lay = QHBoxLayout(frame)
        lay.setContentsMargins(0, 0, 0, 12)
        lay.setSpacing(0)
        self._tab_group = QButtonGroup(frame)
        self._tab_group.setExclusive(True)
        self._tab_games = QPushButton("GAMES", frame)
        self._tab_games.setObjectName("MgrTabBtn")
        self._tab_games.setCheckable(True)
        self._tab_games.setChecked(True)
        self._tab_games.setCursor(Qt.CursorShape.PointingHandCursor)
        self._tab_games.clicked.connect(lambda: self._stack.setCurrentIndex(0))
        self._tab_group.addButton(self._tab_games)
        lay.addWidget(self._tab_games)
        self._tab_themes = QPushButton("THEMES", frame)
        self._tab_themes.setObjectName("MgrTabBtn")
        self._tab_themes.setCheckable(True)
        self._tab_themes.setCursor(Qt.CursorShape.PointingHandCursor)
        self._tab_themes.clicked.connect(lambda: self._stack.setCurrentIndex(1))
        self._tab_group.addButton(self._tab_themes)
        lay.addWidget(self._tab_themes)
        lay.addStretch(1)
        return frame

    # ── Load / push ─────────────────────────────────────────────────

    def _reload(self, *, prefer_remote: bool, blocking: bool = False,
                check_draft: bool = False) -> None:
        if self._loading:
            return
        self._loading = True
        self._set_status("loading", "● ĐANG TẢI...")
        self._reload_btn.setEnabled(False)
        worker = _ConfigLoadWorker(prefer_remote, self)
        worker.finished_ok.connect(
            lambda g, t: self._on_reload_ok(g, t, check_draft=check_draft)
        )
        worker.failed.connect(self._on_reload_failed)
        self._load_worker = worker
        if blocking:
            self._loading_dlg = LoadingDialog(self)
            worker.start()
            self._loading_dlg.exec()
            self._loading_dlg = None
        else:
            worker.start()

    def _on_reload_ok(self, games_raw: dict, themes_raw: dict, *,
                      check_draft: bool = False) -> None:
        if self._loading_dlg is not None:
            self._loading_dlg.hide()
            self._loading_dlg.accept()
        self._games_raw = games_raw
        self._themes_raw = themes_raw

        restored = False
        if check_draft:
            restored = self._maybe_restore_draft()
        if not restored:
            self.games_editor.load(self._games_raw)
            self.themes_editor.load(self._themes_raw)

        self._loading = False
        self._reload_btn.setEnabled(True)
        self._draft_armed = True
        self._update_status_chip()
        self._update_dirty_count_chip()
        self._push_btn.setEnabled(self._is_dirty())

    def _on_reload_failed(self, msg: str) -> None:
        if self._loading_dlg is not None:
            self._loading_dlg.hide()
            self._loading_dlg.accept()
        self._loading = False
        self._reload_btn.setEnabled(True)
        self._set_status("error", "● LỖI TẢI")
        QMessageBox.critical(self, "Lỗi tải config", msg)

    def _on_reload_clicked(self) -> None:
        if self._is_dirty():
            ans = QMessageBox.question(
                self, "Bỏ thay đổi?",
                "Bạn có thay đổi chưa đẩy. Tải lại sẽ ghi đè. Tiếp tục?",
            )
            if ans != QMessageBox.StandardButton.Yes:
                return
        self._delete_draft()
        self._reload(prefer_remote=True, blocking=True)

    def _on_push_clicked(self) -> None:
        if self._pushing or not self._is_dirty():
            return
        games_summary = self.games_editor.diff_summary()
        themes_summary = self.themes_editor.diff_summary()
        combined = {
            "added": games_summary["added"] + themes_summary["added"],
            "modified": games_summary["modified"] + themes_summary["modified"],
            "deleted": games_summary["deleted"] + themes_summary["deleted"],
        }
        dlg = _PushPreviewDialog(combined, "chore: update config via WGZ manager", self)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        msg = dlg.message() or "chore: update config via WGZ manager"

        out_games = dict(self._games_raw)
        self.games_editor.dump_into(out_games)
        out_themes = self.themes_editor.dump()

        self._pushing = True
        self._set_status("pushing", "● ĐANG ĐẨY...")
        self._push_btn.setEnabled(False)
        self._reload_btn.setEnabled(False)

        self._push_worker = PushConfigWorker(out_games, out_themes, msg, self)
        self._push_worker.status.connect(self._on_push_status)
        self._push_worker.finished_ok.connect(self._on_push_ok)
        self._push_worker.failed.connect(self._on_push_failed)
        self._loading_dlg = LoadingDialog(self)
        self._push_worker.start()
        self._loading_dlg.exec()
        self._loading_dlg = None

    def _on_push_status(self, text: str) -> None:
        log.info("Push: %s", text)
        self._set_status("pushing", f"● {text.upper()}")

    def _on_push_ok(self) -> None:
        if self._loading_dlg is not None:
            self._loading_dlg.hide()
            self._loading_dlg.accept()
        self._pushing = False
        self.games_editor.mark_clean()
        self.themes_editor.mark_clean()
        self._reload_btn.setEnabled(True)
        self._delete_draft()
        self._set_status("clean", "● ĐÃ ĐỒNG BỘ")
        self._update_dirty_count_chip()
        self._push_btn.setEnabled(False)
        QMessageBox.information(
            self, "Thành công",
            "Đã đẩy config lên Server.\n"
            "Khởi động lại app (hoặc bấm Refresh ở Thư Viện) để thấy thay đổi.",
        )

    def _on_push_failed(self, err: str) -> None:
        if self._loading_dlg is not None:
            self._loading_dlg.hide()
            self._loading_dlg.accept()
        self._pushing = False
        self._reload_btn.setEnabled(True)
        self._push_btn.setEnabled(self._is_dirty())
        self._set_status("error", "● LỖI ĐẨY")
        QMessageBox.critical(self, "Đẩy thất bại", err)

    # ── Dirty / status ──────────────────────────────────────────────

    def _is_dirty(self) -> bool:
        return self.games_editor.dirty_count() > 0 or self.themes_editor.dirty_count() > 0

    def _on_any_change(self) -> None:
        if self._pushing:
            return
        self._update_status_chip()
        self._update_dirty_count_chip()
        self._push_btn.setEnabled(self._is_dirty())
        if self._draft_armed:
            self._autosave_timer.start()

    def _update_status_chip(self) -> None:
        if self._is_dirty():
            self._set_status("dirty", "● CHƯA ĐỒNG BỘ")
        else:
            self._set_status("clean", "● ĐÃ ĐỒNG BỘ")

    def _update_dirty_count_chip(self) -> None:
        n = self.games_editor.dirty_count() + self.themes_editor.dirty_count()
        if n == 0:
            self._dirty_count_chip.setVisible(False)
        else:
            self._dirty_count_chip.setText(f"{n} thay đổi")
            self._dirty_count_chip.setVisible(True)

    def _set_status(self, state: str, text: str) -> None:
        self._status_chip.setText(text)
        self._status_chip.setProperty("state", state)
        self._status_chip.style().unpolish(self._status_chip)
        self._status_chip.style().polish(self._status_chip)

    # ── Autosave draft ──────────────────────────────────────────────

    def _write_draft(self) -> None:
        if self._pushing or self._loading or not self._is_dirty():
            self._delete_draft()
            return
        out_games = dict(self._games_raw)
        self.games_editor.dump_into(out_games)
        out_themes = self.themes_editor.dump()
        payload = {
            "saved_at": datetime.now().isoformat(timespec="seconds"),
            "games": out_games,
            "themes": out_themes,
        }
        try:
            p = _draft_path()
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        except Exception:
            log.exception("Draft autosave failed")

    def _delete_draft(self) -> None:
        try:
            p = _draft_path()
            if p.exists():
                p.unlink()
        except Exception:
            log.exception("Draft delete failed")

    def _maybe_restore_draft(self) -> bool:
        p = _draft_path()
        if not p.exists():
            return False
        try:
            draft = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            log.exception("Draft read failed; discarding")
            self._delete_draft()
            return False
        when = draft.get("saved_at") or "?"
        ans = QMessageBox.question(
            self, "Khôi phục bản nháp?",
            f"Tìm thấy bản nháp lúc {when} chưa đẩy lên Server.\n"
            "Khôi phục để tiếp tục chỉnh sửa?",
        )
        if ans != QMessageBox.StandardButton.Yes:
            self._delete_draft()
            return False
        draft_games = draft.get("games") or self._games_raw
        draft_themes = draft.get("themes") or self._themes_raw
        # Load server snapshot as baseline first
        self.games_editor.load(self._games_raw)
        self.themes_editor.load(self._themes_raw)
        # Overlay draft state
        self.games_editor._games = {
            k: v for k, v in draft_games.items()
            if k not in _RESERVED_GAME_KEYS and isinstance(v, dict)
        }
        self.games_editor._order = [
            k for k in draft_games.keys()
            if k not in _RESERVED_GAME_KEYS and isinstance(draft_games[k], dict)
        ]
        self.games_editor._rebuild()
        themes_clean: dict[str, dict] = {}
        for key, value in (draft_themes or {}).items():
            if isinstance(value, dict):
                themes_clean[str(key)] = {
                    "image": str(value.get("image") or ""),
                    "slideshow": [str(x) for x in (value.get("slideshow") or [])],
                    "trailer_url": str(value.get("trailer_url") or ""),
                }
        self.themes_editor._themes = themes_clean
        self.themes_editor._order = list(themes_clean.keys())
        self.themes_editor._rebuild()
        self.themes_editor.keys_changed.emit()
        return True
