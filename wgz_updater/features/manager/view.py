"""Tab 4 — Config Manager.

Edit `CapNhatNightReignMod.json` (games + download parts) and `game_themes.json`
(hero image, slideshow, trailer), then push the result back to the source repo
via the GitHub Contents API.

Local edits are kept in memory until the user pushes. Pushing replaces both
remote files in a single worker pass.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QIntValidator
from PyQt6.QtWidgets import (
    QButtonGroup,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QScrollArea,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from ...core.http import get_json
from ...core.paths import (
    CONFIG_BUNDLED,
    CONFIG_LOCAL,
    GITHUB_JSON_URL,
    GITHUB_THEMES_URL,
    THEMES_BUNDLED_CANDIDATES,
    THEMES_LOCAL,
)
from .github_writer import PushConfigWorker

log = logging.getLogger(__name__)

_RESERVED_GAME_KEYS = {"updater", "game_themes.json"}
_TYPE_CHOICES = ("zip", "rar", "exe")


# ════════════════════════════════════════════════════════════════════
# I/O helpers
# ════════════════════════════════════════════════════════════════════

def _read_json(*candidates) -> dict:
    for path in candidates:
        if path and path.exists():
            try:
                return json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                log.exception("Read failed: %s", path)
    return {}


def _load_games_raw(prefer_remote: bool) -> dict:
    if prefer_remote:
        try:
            return get_json(GITHUB_JSON_URL, cachebust=True)
        except Exception:
            log.warning("Remote games config fetch failed; using local cache")
    return _read_json(CONFIG_LOCAL, CONFIG_BUNDLED)


def _load_themes_raw(prefer_remote: bool) -> dict:
    if prefer_remote:
        try:
            return get_json(GITHUB_THEMES_URL, cachebust=True)
        except Exception:
            log.warning("Remote themes fetch failed; using local cache")
    return _read_json(THEMES_LOCAL, *THEMES_BUNDLED_CANDIDATES)


# ════════════════════════════════════════════════════════════════════
# URL list repeater — used for download parts AND theme slideshow
# ════════════════════════════════════════════════════════════════════

class _UrlListEditor(QFrame):
    """Vertical list of editable URL rows with add/remove and index labels."""

    changed = pyqtSignal()

    def __init__(self, caption: str, placeholder: str = "https://...", parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("MgrUrlListWrap")
        self._placeholder = placeholder
        self._rows: list[tuple[QLineEdit, QPushButton, QLabel]] = []

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(6)

        head = QHBoxLayout()
        head.setContentsMargins(0, 0, 0, 0)
        cap = QLabel(caption, self)
        cap.setObjectName("MgrSectionCaption")
        head.addWidget(cap)
        head.addStretch(1)
        add = QPushButton("+ THÊM", self)
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
        # Clear leftover row containers
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
        out: list[str] = []
        for edit, _, _ in self._rows:
            v = edit.text().strip()
            if v:
                out.append(v)
        return out

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

    def _remove_row(self, row: QFrame, edit: QLineEdit, btn: QPushButton, idx: QLabel) -> None:
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


# ════════════════════════════════════════════════════════════════════
# Games editor
# ════════════════════════════════════════════════════════════════════

class _GamesEditor(QWidget):
    """Left: game inventory list + add/remove. Right: full-schema editor."""

    changed = pyqtSignal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._games: dict[str, dict] = {}      # id -> game dict
        self._order: list[str] = []            # ordered IDs (preserves JSON order)
        self._current_id: str | None = None
        self._suppress = False

        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._build_left(), 0)
        root.addWidget(self._build_right(), 1)

    # ── Left rail ───────────────────────────────────────────────────

    def _build_left(self) -> QWidget:
        rail = QFrame(self)
        rail.setObjectName("MgrLeftRail")
        rail.setFixedWidth(280)
        lay = QVBoxLayout(rail)
        lay.setContentsMargins(14, 14, 10, 14)
        lay.setSpacing(8)

        head = QHBoxLayout()
        cap = QLabel("// INVENTORY", rail)
        cap.setObjectName("MgrSectionCaption")
        head.addWidget(cap)
        head.addStretch(1)
        add = QPushButton("+ MỚI", rail)
        add.setObjectName("MgrAddBtn")
        add.setCursor(Qt.CursorShape.PointingHandCursor)
        add.clicked.connect(self._on_add_game)
        head.addWidget(add)
        lay.addLayout(head)

        self._list = QListWidget(rail)
        self._list.setObjectName("MgrList")
        self._list.currentItemChanged.connect(self._on_select)
        lay.addWidget(self._list, 1)

        return rail

    # ── Right editor ────────────────────────────────────────────────

    def _build_right(self) -> QWidget:
        host = QFrame(self)
        host.setObjectName("MgrRightHost")
        outer = QVBoxLayout(host)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # Sticky header
        hdr = QFrame(host)
        hdr.setObjectName("MgrEditHeader")
        hlay = QHBoxLayout(hdr)
        hlay.setContentsMargins(18, 12, 18, 12)
        self._title_lbl = QLabel("// EDIT — (chưa chọn)", hdr)
        self._title_lbl.setObjectName("MgrEditTitle")
        hlay.addWidget(self._title_lbl, 1)
        self._del_btn = QPushButton("XOÁ", hdr)
        self._del_btn.setObjectName("MgrDangerBtn")
        self._del_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._del_btn.clicked.connect(self._on_delete_game)
        self._del_btn.setEnabled(False)
        hlay.addWidget(self._del_btn)
        outer.addWidget(hdr)

        # Scrollable form
        scroll = QScrollArea(host)
        scroll.setObjectName("MgrScroll")
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        form_wrap = QWidget()
        form_wrap.setObjectName("MgrFormWrap")
        form = QVBoxLayout(form_wrap)
        form.setContentsMargins(18, 14, 18, 18)
        form.setSpacing(10)

        self._field_id = QLineEdit(form_wrap)
        self._field_id.setObjectName("MgrInput")
        self._field_id.setValidator(QIntValidator(1, 999999, self._field_id))
        self._field_id.setPlaceholderText("Số nguyên (vd: 5)")
        self._field_id.editingFinished.connect(self._on_id_changed)
        form.addLayout(self._labeled("ID", self._field_id,
                                     hint="Khoá định danh trong JSON. Phải là số duy nhất."))

        self._field_name = self._mk_input("Tên hiển thị")
        form.addLayout(self._labeled("TÊN", self._field_name))

        self._field_game = self._mk_input("vd: Elden Ring Nightreign")
        form.addLayout(self._labeled("GAME", self._field_game,
                                     hint="Khớp với key trong Themes để dùng chung hero image."))

        self._field_version = self._mk_input("vd: v1.4.0")
        form.addLayout(self._labeled("VERSION", self._field_version))

        self._field_type = QComboBox(form_wrap)
        self._field_type.setObjectName("MgrCombo")
        self._field_type.setEditable(True)
        self._field_type.addItems(_TYPE_CHOICES)
        self._field_type.currentTextChanged.connect(self._mark_changed)
        form.addLayout(self._labeled("TYPE", self._field_type))

        self._field_tag = self._mk_input("vd: UPD / NEW / null")
        form.addLayout(self._labeled("TAG", self._field_tag))

        self._field_password = self._mk_input("vd: daominha.com")
        form.addLayout(self._labeled("PASSWORD", self._field_password))

        self._field_launch = self._mk_input("vd: Game/start.exe")
        form.addLayout(self._labeled("LAUNCH FILE", self._field_launch))

        self._field_path_guide = QPlainTextEdit(form_wrap)
        self._field_path_guide.setObjectName("MgrTextArea")
        self._field_path_guide.setFixedHeight(72)
        self._field_path_guide.textChanged.connect(self._mark_changed)
        form.addLayout(self._labeled("PATH GUIDE", self._field_path_guide,
                                     hint="Hướng dẫn người dùng chọn thư mục cài."))

        self._field_delete_before = QPlainTextEdit(form_wrap)
        self._field_delete_before.setObjectName("MgrTextArea")
        self._field_delete_before.setFixedHeight(62)
        self._field_delete_before.setPlaceholderText("Mỗi dòng 1 đường dẫn cần xoá")
        self._field_delete_before.textChanged.connect(self._mark_changed)
        form.addLayout(self._labeled("DELETE BEFORE EXTRACT", self._field_delete_before,
                                     hint="Mỗi dòng = một path tương đối, xoá trước khi giải nén."))

        self._field_urls = _UrlListEditor("// DOWNLOAD PARTS", parent=form_wrap)
        self._field_urls.changed.connect(self._mark_changed)
        form.addWidget(self._field_urls)

        form.addStretch(1)
        scroll.setWidget(form_wrap)
        outer.addWidget(scroll, 1)

        self._set_editor_enabled(False)
        return host

    def _mk_input(self, placeholder: str) -> QLineEdit:
        e = QLineEdit(self)
        e.setObjectName("MgrInput")
        e.setPlaceholderText(placeholder)
        e.textEdited.connect(self._mark_changed)
        return e

    def _labeled(self, label: str, widget: QWidget, *, hint: str | None = None) -> QVBoxLayout:
        col = QVBoxLayout()
        col.setContentsMargins(0, 0, 0, 0)
        col.setSpacing(3)
        lbl = QLabel(label, self)
        lbl.setObjectName("MgrFieldLabel")
        col.addWidget(lbl)
        col.addWidget(widget)
        if hint:
            h = QLabel(hint, self)
            h.setObjectName("MgrFieldHint")
            h.setWordWrap(True)
            col.addWidget(h)
        return col

    # ── Data plumbing ───────────────────────────────────────────────

    def load(self, games_raw: dict) -> None:
        """Accepts the FULL raw dict (including `updater`) and extracts games."""
        self._games = {}
        self._order = []
        for key, value in games_raw.items():
            if key in _RESERVED_GAME_KEYS or not isinstance(value, dict):
                continue
            self._games[str(key)] = dict(value)
            self._order.append(str(key))
        self._refresh_list()
        if self._order:
            self._list.setCurrentRow(0)
        else:
            self._clear_form()

    def dump_into(self, games_raw: dict) -> None:
        """Write current state back into games_raw (preserves `updater` etc.)."""
        for key in list(games_raw.keys()):
            if key not in _RESERVED_GAME_KEYS:
                del games_raw[key]
        for gid in self._order:
            games_raw[gid] = self._games[gid]

    # ── List management ─────────────────────────────────────────────

    def _refresh_list(self) -> None:
        self._suppress = True
        self._list.clear()
        for i, gid in enumerate(self._order, start=1):
            name = self._games[gid].get("name") or "(không tên)"
            # Enhanced: Show download parts information with better handling
            urls = self._games[gid].get("urls", [])
            download_count = len(urls)
            if download_count > 0:
                # Show count and preview of first 2 URLs with better filename extraction
                preview_urls = urls[:2]
                preview_names = []
                for url in preview_urls:
                    # Extract filename from URL, handling various cases
                    filename = url.split("/")[-1]
                    # Remove query parameters and fragments
                    filename = filename.split("?")[0].split("#")[0]
                    # If filename is empty, use a placeholder
                    if not filename:
                        filename = "unknown"
                    preview_names.append(filename)
                preview_text = ", ".join(preview_names)
                if download_count > 2:
                    preview_text += f" (+{download_count - 2} more)"
                # Limit total length to prevent overly wide items
                if len(preview_text) > 50:
                    preview_text = preview_text[:47] + "..."
                item_text = f"  {i:02d}    {name}  [{download_count} parts: {preview_text}]"
            else:
                item_text = f"  {i:02d}    {name}  [No download parts]"
            item = QListWidgetItem(item_text)
            item.setData(Qt.ItemDataRole.UserRole, gid)
            self._list.addItem(item)
        self._suppress = False

    def _on_select(self, current: QListWidgetItem | None, _prev) -> None:
        if self._suppress or current is None:
            return
        # Flush pending edits on previous selection
        self._flush_form()
        gid = current.data(Qt.ItemDataRole.UserRole)
        self._current_id = gid
        self._populate_form(self._games[gid])
        self._set_editor_enabled(True)
        self._del_btn.setEnabled(True)

    def _on_add_game(self) -> None:
        # Next free numeric ID
        used = {int(g) for g in self._order if g.isdigit()}
        new_id = "1"
        n = 1
        while n in used:
            n += 1
        new_id = str(n)
        self._games[new_id] = {
            "name": "Game mới",
            "url": "",
            "version": "",
            "game": "",
            "type": "zip",
            "password": None,
            "delete_before_extract": [],
            "path_guide": "",
            "launch_file": None,
            "urls": [],
        }
        self._order.append(new_id)
        self._refresh_list()
        # Select the new one
        for i in range(self._list.count()):
            if self._list.item(i).data(Qt.ItemDataRole.UserRole) == new_id:
                self._list.setCurrentRow(i)
                break
        self.changed.emit()

    def _on_delete_game(self) -> None:
        if not self._current_id:
            return
        gid = self._current_id
        name = self._games[gid].get("name") or gid
        ans = QMessageBox.question(
            self,
            "Xác nhận xoá",
            f"Xoá game '{name}' (id: {gid})?\nThao tác này chỉ ghi vào bộ nhớ — "
            f"chưa đẩy lên GitHub cho đến khi bạn bấm PUSH.",
        )
        if ans != QMessageBox.StandardButton.Yes:
            return
        self._order.remove(gid)
        del self._games[gid]
        self._current_id = None
        self._refresh_list()
        if self._order:
            self._list.setCurrentRow(0)
        else:
            self._clear_form()
        self.changed.emit()

    # ── Form ↔ data ─────────────────────────────────────────────────

    def _populate_form(self, game: dict) -> None:
        self._suppress = True
        try:
            self._field_id.setText(str(self._current_id or ""))
            self._field_name.setText(str(game.get("name") or ""))
            self._field_game.setText(str(game.get("game") or ""))
            self._field_version.setText(str(game.get("version") or ""))
            tp = str(game.get("type") or "zip")
            idx = self._field_type.findText(tp)
            if idx >= 0:
                self._field_type.setCurrentIndex(idx)
            else:
                self._field_type.setEditText(tp)
            self._field_tag.setText("" if game.get("tag") is None else str(game.get("tag")))
            self._field_password.setText(
                "" if game.get("password") is None else str(game.get("password"))
            )
            self._field_launch.setText(
                "" if game.get("launch_file") is None else str(game.get("launch_file"))
            )
            self._field_path_guide.setPlainText(str(game.get("path_guide") or ""))
            dbe = game.get("delete_before_extract") or []
            self._field_delete_before.setPlainText("\n".join(str(x) for x in dbe))
            # urls or single url
            urls = list(game.get("urls") or [])
            if not urls and game.get("url"):
                urls = [str(game["url"])]
            self._field_urls.set_values(urls)
            self._title_lbl.setText(f"// EDIT — {game.get('name') or '(không tên)'}")
        finally:
            self._suppress = False

    def _flush_form(self) -> None:
        if not self._current_id or self._suppress:
            return
        game = self._games.get(self._current_id)
        if game is None:
            return
        game["name"] = self._field_name.text().strip()
        game["game"] = self._field_game.text().strip()
        game["version"] = self._field_version.text().strip()
        game["type"] = self._field_type.currentText().strip() or "zip"
        tag = self._field_tag.text().strip()
        game["tag"] = tag or None
        pwd = self._field_password.text().strip()
        game["password"] = pwd or None
        launch = self._field_launch.text().strip()
        game["launch_file"] = launch or None
        game["path_guide"] = self._field_path_guide.toPlainText().strip()
        dbe_raw = self._field_delete_before.toPlainText().splitlines()
        game["delete_before_extract"] = [s.strip() for s in dbe_raw if s.strip()]
        urls = self._field_urls.values()
        # Normalize to `urls`; clear legacy `url` so we don't duplicate data
        game["urls"] = urls
        game.pop("url", None)
        # Sync list label if name changed
        self._sync_list_row_for(self._current_id)

    def _sync_list_row_for(self, gid: str) -> None:
        for i in range(self._list.count()):
            it = self._list.item(i)
            if it.data(Qt.ItemDataRole.UserRole) == gid:
                name = self._games[gid].get("name") or "(không tên)"
                it.setText(f"  {i + 1:02d}    {name}")
                return

    def _on_id_changed(self) -> None:
        if self._suppress or not self._current_id:
            return
        new_id = self._field_id.text().strip()
        if not new_id or new_id == self._current_id:
            return
        if new_id in self._games:
            QMessageBox.warning(self, "Trùng ID", f"ID '{new_id}' đã tồn tại.")
            self._field_id.setText(self._current_id)
            return
        old_id = self._current_id
        self._games[new_id] = self._games.pop(old_id)
        i = self._order.index(old_id)
        self._order[i] = new_id
        self._current_id = new_id
        self._refresh_list()
        for j in range(self._list.count()):
            if self._list.item(j).data(Qt.ItemDataRole.UserRole) == new_id:
                self._list.setCurrentRow(j)
                break
        self.changed.emit()

    def _mark_changed(self, *_args) -> None:
        if self._suppress:
            return
        self._flush_form()
        self.changed.emit()

    def _clear_form(self) -> None:
        self._suppress = True
        try:
            for f in (self._field_id, self._field_name, self._field_game,
                      self._field_version, self._field_tag, self._field_password,
                      self._field_launch):
                f.clear()
            self._field_type.setCurrentIndex(0)
            self._field_path_guide.clear()
            self._field_delete_before.clear()
            self._field_urls.set_values([])
            self._title_lbl.setText("// EDIT — (chưa chọn)")
            self._del_btn.setEnabled(False)
            self._set_editor_enabled(False)
        finally:
            self._suppress = False

    def _set_editor_enabled(self, enabled: bool) -> None:
        for w in (self._field_id, self._field_name, self._field_game,
                  self._field_version, self._field_type, self._field_tag,
                  self._field_password, self._field_launch,
                  self._field_path_guide, self._field_delete_before,
                  self._field_urls):
            w.setEnabled(enabled)


# ════════════════════════════════════════════════════════════════════
# Themes editor
# ════════════════════════════════════════════════════════════════════

class _ThemesEditor(QWidget):
    """Same list+form pattern; themes are keyed by string (usually game name)."""

    changed = pyqtSignal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._themes: dict[str, dict] = {}
        self._order: list[str] = []
        self._current_key: str | None = None
        self._suppress = False

        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.addWidget(self._build_left(), 0)
        root.addWidget(self._build_right(), 1)

    def _build_left(self) -> QWidget:
        rail = QFrame(self)
        rail.setObjectName("MgrLeftRail")
        rail.setFixedWidth(280)
        lay = QVBoxLayout(rail)
        lay.setContentsMargins(14, 14, 10, 14)
        lay.setSpacing(8)

        head = QHBoxLayout()
        cap = QLabel("// THEMES", rail)
        cap.setObjectName("MgrSectionCaption")
        head.addWidget(cap)
        head.addStretch(1)
        add = QPushButton("+ MỚI", rail)
        add.setObjectName("MgrAddBtn")
        add.setCursor(Qt.CursorShape.PointingHandCursor)
        add.clicked.connect(self._on_add_theme)
        head.addWidget(add)
        lay.addLayout(head)

        self._list = QListWidget(rail)
        self._list.setObjectName("MgrList")
        self._list.currentItemChanged.connect(self._on_select)
        lay.addWidget(self._list, 1)
        return rail

    def _build_right(self) -> QWidget:
        host = QFrame(self)
        host.setObjectName("MgrRightHost")
        outer = QVBoxLayout(host)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        hdr = QFrame(host)
        hdr.setObjectName("MgrEditHeader")
        hlay = QHBoxLayout(hdr)
        hlay.setContentsMargins(18, 12, 18, 12)
        self._title_lbl = QLabel("// EDIT — (chưa chọn)", hdr)
        self._title_lbl.setObjectName("MgrEditTitle")
        hlay.addWidget(self._title_lbl, 1)
        self._del_btn = QPushButton("XOÁ", hdr)
        self._del_btn.setObjectName("MgrDangerBtn")
        self._del_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._del_btn.clicked.connect(self._on_delete_theme)
        self._del_btn.setEnabled(False)
        hlay.addWidget(self._del_btn)
        outer.addWidget(hdr)

        scroll = QScrollArea(host)
        scroll.setObjectName("MgrScroll")
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        form_wrap = QWidget()
        form_wrap.setObjectName("MgrFormWrap")
        form = QVBoxLayout(form_wrap)
        form.setContentsMargins(18, 14, 18, 18)
        form.setSpacing(10)

        self._field_key = QLineEdit(form_wrap)
        self._field_key.setObjectName("MgrInput")
        self._field_key.setPlaceholderText("vd: Elden Ring Nightreign")
        self._field_key.editingFinished.connect(self._on_key_changed)
        form.addLayout(self._labeled("KEY", self._field_key,
                                     hint="Khớp với field 'game' trong Games."))

        self._field_image = QLineEdit(form_wrap)
        self._field_image.setObjectName("MgrInput")
        self._field_image.setPlaceholderText("https://... (hero image)")
        self._field_image.textEdited.connect(self._mark_changed)
        form.addLayout(self._labeled("HERO IMAGE", self._field_image))

        self._field_trailer = QLineEdit(form_wrap)
        self._field_trailer.setObjectName("MgrInput")
        self._field_trailer.setPlaceholderText("https://youtube.com/...")
        self._field_trailer.textEdited.connect(self._mark_changed)
        form.addLayout(self._labeled("TRAILER URL", self._field_trailer))

        self._field_slideshow = _UrlListEditor("// SLIDESHOW", parent=form_wrap)
        self._field_slideshow.changed.connect(self._mark_changed)
        form.addWidget(self._field_slideshow)

        form.addStretch(1)
        scroll.setWidget(form_wrap)
        outer.addWidget(scroll, 1)

        self._set_editor_enabled(False)
        return host

    def _labeled(self, label: str, widget: QWidget, *, hint: str | None = None) -> QVBoxLayout:
        col = QVBoxLayout()
        col.setContentsMargins(0, 0, 0, 0)
        col.setSpacing(3)
        lbl = QLabel(label, self)
        lbl.setObjectName("MgrFieldLabel")
        col.addWidget(lbl)
        col.addWidget(widget)
        if hint:
            h = QLabel(hint, self)
            h.setObjectName("MgrFieldHint")
            h.setWordWrap(True)
            col.addWidget(h)
        return col

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
        self._refresh_list()
        if self._order:
            self._list.setCurrentRow(0)
        else:
            self._clear_form()

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

    def _refresh_list(self) -> None:
        self._suppress = True
        self._list.clear()
        for i, key in enumerate(self._order, start=1):
            item = QListWidgetItem(f"  {i:02d}    {key}")
            item.setData(Qt.ItemDataRole.UserRole, key)
            self._list.addItem(item)
        self._suppress = False

    def _on_select(self, current: QListWidgetItem | None, _prev) -> None:
        if self._suppress or current is None:
            return
        self._flush_form()
        key = current.data(Qt.ItemDataRole.UserRole)
        self._current_key = key
        self._populate_form(self._themes[key])
        self._set_editor_enabled(True)
        self._del_btn.setEnabled(True)

    def _on_add_theme(self) -> None:
        key, ok = QInputDialog.getText(
            self, "Theme mới", "Tên key (thường khớp với field 'game'):"
        )
        key = (key or "").strip()
        if not ok or not key:
            return
        if key in self._themes:
            QMessageBox.warning(self, "Trùng key", f"Theme '{key}' đã tồn tại.")
            return
        self._themes[key] = {"image": "", "slideshow": [], "trailer_url": ""}
        self._order.append(key)
        self._refresh_list()
        for i in range(self._list.count()):
            if self._list.item(i).data(Qt.ItemDataRole.UserRole) == key:
                self._list.setCurrentRow(i)
                break
        self.changed.emit()

    def _on_delete_theme(self) -> None:
        if not self._current_key:
            return
        ans = QMessageBox.question(
            self, "Xác nhận xoá",
            f"Xoá theme '{self._current_key}'?\nChưa đẩy lên GitHub cho đến khi bạn bấm PUSH.",
        )
        if ans != QMessageBox.StandardButton.Yes:
            return
        self._order.remove(self._current_key)
        del self._themes[self._current_key]
        self._current_key = None
        self._refresh_list()
        if self._order:
            self._list.setCurrentRow(0)
        else:
            self._clear_form()
        self.changed.emit()

    def _populate_form(self, theme: dict) -> None:
        self._suppress = True
        try:
            self._field_key.setText(self._current_key or "")
            self._field_image.setText(str(theme.get("image") or ""))
            self._field_trailer.setText(str(theme.get("trailer_url") or ""))
            self._field_slideshow.set_values(
                [str(x) for x in (theme.get("slideshow") or [])]
            )
            self._title_lbl.setText(f"// EDIT — {self._current_key}")
        finally:
            self._suppress = False

    def _flush_form(self) -> None:
        if not self._current_key or self._suppress:
            return
        t = self._themes.get(self._current_key)
        if t is None:
            return
        t["image"] = self._field_image.text().strip()
        t["trailer_url"] = self._field_trailer.text().strip()
        t["slideshow"] = self._field_slideshow.values()

    def _on_key_changed(self) -> None:
        if self._suppress or not self._current_key:
            return
        new_key = self._field_key.text().strip()
        if not new_key or new_key == self._current_key:
            return
        if new_key in self._themes:
            QMessageBox.warning(self, "Trùng key", f"Theme '{new_key}' đã tồn tại.")
            self._field_key.setText(self._current_key)
            return
        old_key = self._current_key
        self._themes[new_key] = self._themes.pop(old_key)
        i = self._order.index(old_key)
        self._order[i] = new_key
        self._current_key = new_key
        self._refresh_list()
        for j in range(self._list.count()):
            if self._list.item(j).data(Qt.ItemDataRole.UserRole) == new_key:
                self._list.setCurrentRow(j)
                break
        self.changed.emit()

    def _mark_changed(self, *_args) -> None:
        if self._suppress:
            return
        self._flush_form()
        self.changed.emit()

    def _clear_form(self) -> None:
        self._suppress = True
        try:
            self._field_key.clear()
            self._field_image.clear()
            self._field_trailer.clear()
            self._field_slideshow.set_values([])
            self._title_lbl.setText("// EDIT — (chưa chọn)")
            self._del_btn.setEnabled(False)
            self._set_editor_enabled(False)
        finally:
            self._suppress = False

    def _set_editor_enabled(self, enabled: bool) -> None:
        for w in (self._field_key, self._field_image, self._field_trailer,
                  self._field_slideshow):
            w.setEnabled(enabled)


# ════════════════════════════════════════════════════════════════════
# Top-level Manager view
# ════════════════════════════════════════════════════════════════════

class ManagerView(QWidget):
    """Tab 4 — orchestrates the games + themes editors and the GitHub push."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("MgrView")

        self._games_raw: dict = {}     # full file incl. `updater`
        self._themes_raw: dict = {}    # full file
        self._dirty = False
        self._pushing = False
        self._push_worker: PushConfigWorker | None = None

        outer = QVBoxLayout(self)
        outer.setContentsMargins(20, 14, 20, 14)
        outer.setSpacing(0)

        outer.addWidget(self._build_header())
        outer.addWidget(self._build_tab_strip())

        self._stack = QStackedWidget(self)
        self._games_editor = _GamesEditor(self._stack)
        self._themes_editor = _ThemesEditor(self._stack)
        self._stack.addWidget(self._games_editor)
        self._stack.addWidget(self._themes_editor)
        outer.addWidget(self._stack, 1)

        self._games_editor.changed.connect(self._mark_dirty)
        self._themes_editor.changed.connect(self._mark_dirty)

        QTimer.singleShot(0, lambda: self._reload(prefer_remote=True))

    # ── Header (status + actions) ───────────────────────────────────

    def _build_header(self) -> QWidget:
        frame = QFrame(self)
        frame.setObjectName("MgrHeader")
        lay = QHBoxLayout(frame)
        lay.setContentsMargins(0, 0, 0, 14)
        lay.setSpacing(10)

        title = QLabel("// CONFIG MANAGER", frame)
        title.setObjectName("MgrTitle")
        lay.addWidget(title)

        sub = QLabel("· đồng bộ về repo", frame)
        sub.setObjectName("MgrSubtitle")
        lay.addWidget(sub)

        lay.addStretch(1)

        self._status_chip = QLabel("● ĐÃ ĐỒNG BỘ", frame)
        self._status_chip.setObjectName("MgrStatusChip")
        self._status_chip.setProperty("state", "clean")
        lay.addWidget(self._status_chip)

        self._reload_btn = QPushButton("↻ TẢI LẠI", frame)
        self._reload_btn.setObjectName("MgrSecondaryBtn")
        self._reload_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._reload_btn.clicked.connect(self._on_reload_clicked)
        lay.addWidget(self._reload_btn)

        self._push_btn = QPushButton("⇡ ĐẨY LÊN GITHUB", frame)
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

    def _reload(self, *, prefer_remote: bool) -> None:
        self._set_status("loading", "● ĐANG TẢI...")
        try:
            self._games_raw = _load_games_raw(prefer_remote) or {}
            self._themes_raw = _load_themes_raw(prefer_remote) or {}
        except Exception as exc:
            log.exception("Config load failed")
            QMessageBox.critical(self, "Lỗi tải config", str(exc))
            self._set_status("error", "● LỖI TẢI")
            return
        self._games_editor.load(self._games_raw)
        self._themes_editor.load(self._themes_raw)
        self._dirty = False
        self._update_status_chip()
        self._push_btn.setEnabled(False)

    def _on_reload_clicked(self) -> None:
        if self._dirty:
            ans = QMessageBox.question(
                self, "Bỏ thay đổi?",
                "Bạn có thay đổi chưa đẩy. Tải lại sẽ ghi đè. Tiếp tục?",
            )
            if ans != QMessageBox.StandardButton.Yes:
                return
        self._reload(prefer_remote=True)

    def _on_push_clicked(self) -> None:
        if self._pushing or not self._dirty:
            return
        # Flush any pending field edits before serializing
        self._games_editor._flush_form()
        self._themes_editor._flush_form()

        msg, ok = QInputDialog.getText(
            self, "Commit message",
            "Ghi chú thay đổi (sẽ là commit message trên GitHub):",
            text="chore: update config via WGZ manager",
        )
        if not ok:
            return
        msg = (msg or "").strip() or "chore: update config via WGZ manager"

        # Assemble final raw dicts
        out_games = dict(self._games_raw)
        self._games_editor.dump_into(out_games)
        out_themes = self._themes_editor.dump()

        self._pushing = True
        self._set_status("pushing", "● ĐANG ĐẨY...")
        self._push_btn.setEnabled(False)
        self._reload_btn.setEnabled(False)

        self._push_worker = PushConfigWorker(out_games, out_themes, msg, self)
        self._push_worker.status.connect(self._on_push_status)
        self._push_worker.finished_ok.connect(self._on_push_ok)
        self._push_worker.failed.connect(self._on_push_failed)
        self._push_worker.start()

    def _on_push_status(self, text: str) -> None:
        log.info("Push: %s", text)
        self._set_status("pushing", f"● {text.upper()}")

    def _on_push_ok(self) -> None:
        self._pushing = False
        self._dirty = False
        self._reload_btn.setEnabled(True)
        self._set_status("clean", "● ĐÃ ĐỒNG BỘ")
        QMessageBox.information(
            self, "Thành công",
            "Đã đẩy config lên GitHub.\n"
            "Khởi động lại app (hoặc bấm Refresh ở Thư Viện) để thấy thay đổi.",
        )

    def _on_push_failed(self, err: str) -> None:
        self._pushing = False
        self._reload_btn.setEnabled(True)
        self._push_btn.setEnabled(self._dirty)
        self._set_status("error", "● LỖI ĐẨY")
        QMessageBox.critical(self, "Đẩy thất bại", err)

    # ── Dirty / status ──────────────────────────────────────────────

    def _mark_dirty(self) -> None:
        if self._pushing:
            return
        self._dirty = True
        self._update_status_chip()
        self._push_btn.setEnabled(True)

    def _update_status_chip(self) -> None:
        if self._dirty:
            self._set_status("dirty", "● CHƯA ĐỒNG BỘ")
        else:
            self._set_status("clean", "● ĐÃ ĐỒNG BỘ")

    def _set_status(self, state: str, text: str) -> None:
        self._status_chip.setText(text)
        self._status_chip.setProperty("state", state)
        self._status_chip.style().unpolish(self._status_chip)
        self._status_chip.style().polish(self._status_chip)
