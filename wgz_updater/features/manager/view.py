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

from PyQt6.QtCore import QPoint, QSize, Qt, QTimer, pyqtSignal
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
    QMenu,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QScrollArea,
    QStackedWidget,
    QTreeWidget,
    QTreeWidgetItem,
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
    USER_DATA_DIR,
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
# Inventory tree rows
# ════════════════════════════════════════════════════════════════════

class _GroupHeaderRow(QFrame):
    """Top-level row in the inventory tree: chevron + label + count + hover actions."""

    toggle_requested = pyqtSignal()
    add_requested = pyqtSignal()
    menu_requested = pyqtSignal(QPoint)  # global position for the menu

    def __init__(self, label: str, count: int, expanded: bool, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("MgrGroupHeader")
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(8, 0, 6, 0)
        lay.setSpacing(8)

        self._chev = QLabel("▾" if expanded else "▸", self)
        self._chev.setObjectName("MgrGroupChevron")
        self._chev.setFixedWidth(12)
        lay.addWidget(self._chev)

        self._name = QLabel(label, self)
        self._name.setObjectName("MgrGroupName")
        lay.addWidget(self._name, 1)

        self._count = QLabel(str(count), self)
        self._count.setObjectName("MgrGroupCount")
        self._count.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._count.setMinimumWidth(22)
        lay.addWidget(self._count)

        self._add_btn = QPushButton("+", self)
        self._add_btn.setObjectName("MgrGroupAction")
        self._add_btn.setFixedSize(18, 18)
        self._add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._add_btn.setToolTip("Thêm entry vào nhóm này")
        self._add_btn.clicked.connect(self.add_requested.emit)
        self._add_btn.setVisible(False)
        lay.addWidget(self._add_btn)

        self._menu_btn = QPushButton("⋮", self)
        self._menu_btn.setObjectName("MgrGroupAction")
        self._menu_btn.setFixedSize(18, 18)
        self._menu_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._menu_btn.setToolTip("Tác vụ nhóm")
        self._menu_btn.clicked.connect(self._emit_menu)
        self._menu_btn.setVisible(False)
        lay.addWidget(self._menu_btn)

    def _emit_menu(self) -> None:
        self.menu_requested.emit(
            self._menu_btn.mapToGlobal(QPoint(0, self._menu_btn.height()))
        )

    def set_expanded(self, expanded: bool) -> None:
        self._chev.setText("▾" if expanded else "▸")

    def set_count(self, count: int) -> None:
        self._count.setText(str(count))

    def enterEvent(self, event):  # noqa: N802 - Qt API
        self._add_btn.setVisible(True)
        self._menu_btn.setVisible(True)
        super().enterEvent(event)

    def leaveEvent(self, event):  # noqa: N802 - Qt API
        self._add_btn.setVisible(False)
        self._menu_btn.setVisible(False)
        super().leaveEvent(event)

    def mousePressEvent(self, event):  # noqa: N802 - Qt API
        if event.button() == Qt.MouseButton.LeftButton:
            self.toggle_requested.emit()
        super().mousePressEvent(event)


class _GameRow(QFrame):
    """Child row in the inventory tree: index + name + parts-count chip."""

    def __init__(self, index: int, name: str, parts: int, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("MgrChild")
        self.setProperty("selected", "false")

        lay = QHBoxLayout(self)
        lay.setContentsMargins(22, 0, 8, 0)
        lay.setSpacing(8)

        self._idx = QLabel(f"{index:02d}", self)
        self._idx.setObjectName("MgrChildIndex")
        self._idx.setFixedWidth(20)
        lay.addWidget(self._idx)

        self._name = QLabel(name, self)
        self._name.setObjectName("MgrChildName")
        self._name.setMinimumWidth(0)
        lay.addWidget(self._name, 1)

        self._chip = QLabel(str(parts), self)
        self._chip.setObjectName("MgrPartsChip")
        self._chip.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._chip.setMinimumWidth(22)
        self._chip.setVisible(parts > 0)
        lay.addWidget(self._chip)

    def set_index(self, index: int) -> None:
        self._idx.setText(f"{index:02d}")

    def set_name(self, name: str) -> None:
        self._name.setText(name)

    def set_parts(self, parts: int) -> None:
        self._chip.setText(str(parts))
        self._chip.setVisible(parts > 0)

    def set_selected(self, selected: bool) -> None:
        self.setProperty("selected", "true" if selected else "false")
        # Repolish so the QSS attribute selector picks up the new value.
        self.style().unpolish(self)
        self.style().polish(self)


# ════════════════════════════════════════════════════════════════════
# Games editor
# ════════════════════════════════════════════════════════════════════

class _GamesEditor(QWidget):
    """Left: grouped inventory tree + add/remove. Right: full-schema editor."""

    changed = pyqtSignal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._games: dict[str, dict] = {}      # id -> game dict
        self._order: list[str] = []            # ordered IDs (preserves JSON order)
        self._current_id: str | None = None
        self._suppress = False

        # Grouping state
        self._groups: dict[str, list[str]] = {}            # group_key -> ordered gids
        self._collapsed: set[str] = self._load_collapsed()  # group keys collapsed by user
        self._focused_group: str | None = None              # last group the user touched
        self._group_items: dict[str, QTreeWidgetItem] = {}
        self._group_widgets: dict[str, _GroupHeaderRow] = {}
        self._game_items: dict[str, QTreeWidgetItem] = {}
        self._game_widgets: dict[str, _GameRow] = {}

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

        self._tree = QTreeWidget(rail)
        self._tree.setObjectName("MgrTree")
        self._tree.setHeaderHidden(True)
        self._tree.setRootIsDecorated(False)
        self._tree.setIndentation(0)
        self._tree.setItemsExpandable(False)
        self._tree.setExpandsOnDoubleClick(False)
        self._tree.setUniformRowHeights(False)
        self._tree.currentItemChanged.connect(self._on_select)
        lay.addWidget(self._tree, 1)

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
        self._field_game.editingFinished.connect(self._on_game_field_committed)
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
        self._current_id = None
        for key, value in games_raw.items():
            if key in _RESERVED_GAME_KEYS or not isinstance(value, dict):
                continue
            self._games[str(key)] = dict(value)
            self._order.append(str(key))
        self._refresh_list()
        if self._order:
            first_gid = self._order[0]
            if first_gid in self._game_items:
                self._tree.setCurrentItem(self._game_items[first_gid])
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
        self._tree.clear()
        self._group_items.clear()
        self._group_widgets.clear()
        self._game_items.clear()
        self._game_widgets.clear()

        # Build groups dict (preserve first-appearance order)
        self._groups = {}
        for gid in self._order:
            key = (self._games[gid].get("game") or "").strip()
            self._groups.setdefault(key, []).append(gid)

        # Render in first-appearance order; empty-key bucket always last
        ordered_keys = [k for k in self._groups if k != ""]
        if "" in self._groups:
            ordered_keys.append("")

        for key in ordered_keys:
            gids = self._groups[key]
            label = key.upper() if key else "(CHƯA NHÓM)"
            expanded = key not in self._collapsed

            g_item = QTreeWidgetItem(self._tree)
            g_item.setData(0, Qt.ItemDataRole.UserRole, {"kind": "group", "key": key})
            g_item.setFlags(Qt.ItemFlag.ItemIsEnabled)  # not editable-selectable
            g_item.setSizeHint(0, QSize(0, 32))
            g_widget = _GroupHeaderRow(label, len(gids), expanded, self._tree)
            g_widget.toggle_requested.connect(lambda k=key: self._on_group_toggle(k))
            g_widget.add_requested.connect(lambda k=key: self._on_group_add(k))
            g_widget.menu_requested.connect(
                lambda pos, k=key: self._on_group_menu(k, pos)
            )
            self._tree.setItemWidget(g_item, 0, g_widget)
            self._group_items[key] = g_item
            self._group_widgets[key] = g_widget

            for idx, gid in enumerate(gids, start=1):
                c_item = QTreeWidgetItem(g_item)
                c_item.setData(0, Qt.ItemDataRole.UserRole, {"kind": "game", "gid": gid})
                c_item.setSizeHint(0, QSize(0, 28))
                urls = list(self._games[gid].get("urls") or [])
                name = self._games[gid].get("name") or "(không tên)"
                c_widget = _GameRow(idx, name, len(urls), self._tree)
                c_widget.setToolTip(self._build_tooltip(name, urls))
                self._tree.setItemWidget(c_item, 0, c_widget)
                self._game_items[gid] = c_item
                self._game_widgets[gid] = c_widget

            g_item.setExpanded(expanded)

        # Reapply visual selection if a game is still current
        if self._current_id and self._current_id in self._game_widgets:
            self._game_widgets[self._current_id].set_selected(True)

        self._suppress = False

    def _on_select(self, current, previous) -> None:
        if self._suppress:
            return
        # Flush pending edits before switching context
        self._flush_form()

        # Clear visual on previous game row
        if previous is not None:
            prev_data = previous.data(0, Qt.ItemDataRole.UserRole)
            if isinstance(prev_data, dict) and prev_data.get("kind") == "game":
                prev_gid = prev_data.get("gid")
                if prev_gid in self._game_widgets:
                    self._game_widgets[prev_gid].set_selected(False)

        if current is None:
            return
        data = current.data(0, Qt.ItemDataRole.UserRole)
        if not isinstance(data, dict):
            return

        if data.get("kind") == "group":
            # Group rows aren't selectable for editing, but track focus for "+"
            self._focused_group = data.get("key") or ""
            return

        if data.get("kind") == "game":
            gid = data.get("gid")
            if gid not in self._games:
                return
            self._current_id = gid
            self._focused_group = (self._games[gid].get("game") or "").strip()
            self._populate_form(self._games[gid])
            self._set_editor_enabled(True)
            self._del_btn.setEnabled(True)
            if gid in self._game_widgets:
                self._game_widgets[gid].set_selected(True)

    def _on_add_game(self) -> None:
        self._add_new_entry(self._focused_group)

    def _add_new_entry(self, group_key: str | None) -> None:
        used = {int(g) for g in self._order if g.isdigit()}
        n = 1
        while n in used:
            n += 1
        new_id = str(n)
        target = (group_key or "").strip()
        self._games[new_id] = {
            "name": "Game mới",
            "url": "",
            "version": "",
            "game": target,
            "type": "zip",
            "password": None,
            "delete_before_extract": [],
            "path_guide": "",
            "launch_file": None,
            "urls": [],
        }
        self._order.append(new_id)
        # Ensure the target group is expanded so the user sees the new row
        self._collapsed.discard(target)
        self._save_collapsed()
        self._refresh_list()
        self._focused_group = target
        if new_id in self._game_items:
            self._tree.setCurrentItem(self._game_items[new_id])
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
            first_gid = self._order[0]
            if first_gid in self._game_items:
                self._tree.setCurrentItem(self._game_items[first_gid])
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
        widget = self._game_widgets.get(gid)
        if widget is None:
            return
        name = self._games[gid].get("name") or "(không tên)"
        urls = list(self._games[gid].get("urls") or [])
        widget.set_name(name)
        widget.set_parts(len(urls))
        widget.setToolTip(self._build_tooltip(name, urls))

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
        if new_id in self._game_items:
            self._tree.setCurrentItem(self._game_items[new_id])
        self.changed.emit()

    def _on_game_field_committed(self) -> None:
        """When user finishes editing the `game` field, regroup the tree."""
        if self._suppress or not self._current_id:
            return
        gid = self._current_id
        self._refresh_list()
        if gid in self._game_items:
            self._tree.setCurrentItem(self._game_items[gid])

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

    # ── Group operations ────────────────────────────────────────────

    def _build_tooltip(self, name: str, urls: list[str]) -> str:
        if not urls:
            return f"Game: {name}\nNo download parts configured"
        lines = [f"Game: {name}", f"Download Parts ({len(urls)}):"]
        for j, url in enumerate(urls, 1):
            lines.append(f"  {j:02d}. {url}")
        return "\n".join(lines)

    def _on_group_toggle(self, key: str) -> None:
        item = self._group_items.get(key)
        widget = self._group_widgets.get(key)
        if item is None or widget is None:
            return
        expanded = not item.isExpanded()
        item.setExpanded(expanded)
        widget.set_expanded(expanded)
        if expanded:
            self._collapsed.discard(key)
        else:
            self._collapsed.add(key)
        self._focused_group = key
        self._save_collapsed()

    def _on_group_add(self, key: str) -> None:
        self._add_new_entry(key)

    def _on_group_menu(self, key: str, global_pos: QPoint) -> None:
        menu = QMenu(self)
        menu.addAction("Đổi tên nhóm…", lambda: self._on_rename_group(key))
        menu.addAction("Thêm vào nhóm này", lambda: self._on_group_add(key))
        menu.addSeparator()
        menu.addAction("Thu gọn nhóm khác", lambda: self._on_collapse_others(key))
        menu.exec(global_pos)

    def _on_rename_group(self, key: str) -> None:
        new_key, ok = QInputDialog.getText(
            self, "Đổi tên nhóm",
            "Tên nhóm mới (ghi vào trường `game` của mọi entry trong nhóm).\n"
            "Mẹo: trùng với key trong game_themes.json để dùng chung hero image.",
            QLineEdit.EchoMode.Normal,
            key,
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
        self._refresh_list()
        # Re-populate the form so the visible "game" field reflects the new key
        if self._current_id and self._current_id in self._games:
            self._populate_form(self._games[self._current_id])
            if self._current_id in self._game_items:
                self._tree.setCurrentItem(self._game_items[self._current_id])
        self.changed.emit()

    def _on_collapse_others(self, key: str) -> None:
        for k, item in self._group_items.items():
            widget = self._group_widgets.get(k)
            if k == key:
                item.setExpanded(True)
                if widget is not None:
                    widget.set_expanded(True)
                self._collapsed.discard(k)
            else:
                item.setExpanded(False)
                if widget is not None:
                    widget.set_expanded(False)
                self._collapsed.add(k)
        self._focused_group = key
        self._save_collapsed()

    # ── Collapse-state persistence ──────────────────────────────────

    def _collapsed_path(self):
        return USER_DATA_DIR / "manager_groups.json"

    def _load_collapsed(self) -> set[str]:
        p = self._collapsed_path()
        if not p.exists():
            return set()
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            return {str(x) for x in data.get("collapsed", []) if isinstance(x, str)}
        except Exception:
            log.exception("Read collapsed groups state failed")
            return set()

    def _save_collapsed(self) -> None:
        try:
            p = self._collapsed_path()
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(
                json.dumps({"collapsed": sorted(self._collapsed)}, ensure_ascii=False),
                encoding="utf-8",
            )
        except Exception:
            log.exception("Save collapsed groups state failed")


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
