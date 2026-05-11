# Manager Tab — Group Sibling Games by `game` Field (Design)

**Goal:** In the Manager tab inventory rail, merge sibling game entries that share the same `game` field under one expandable header. Each header shows a count badge; each child row shows a small parts-count chip. Hover actions on group headers (rename, add to group, collapse others). Pre-fill `game` when adding a new entry inside a focused group.

**Supersedes:** the inline `[N parts: filename, ...]` annotations added in commits `47b9543`, `38739fb`, `ec8764c`. Per-item tooltip with full URL list is kept (now attached to the new child widget).

## Architecture

- Replace `self._list: QListWidget` in `_GamesEditor._build_left()` with `self._tree: QTreeWidget` (single column, header hidden, custom indentation ~14px, `setItemsExpandable(False)` — chevron is part of our custom header widget).
- Two item types, rendered via `setItemWidget()`:
  - **Top-level (group):** stores `{"kind": "group", "key": <game_field_value>}`. Renders `_GroupHeaderRow`: chevron + group name + count badge + hover-revealed `+` and `⋮` buttons.
  - **Child (game):** stores `{"kind": "game", "gid": <id>}`. Renders `_GameRow`: 2-digit index, name, small parts-count chip on the right.
- `self._order` (JSON order of `gid`s) stays the source of truth for `dump_into()`. A derived `self._groups: dict[str, list[str]]` is rebuilt in `_refresh_list()`.
- `self._collapsed: set[str]` of group keys, persisted to `USER_DATA_DIR/manager_groups.json` on toggle (lazy load on first `_refresh_list`).

## Grouping rules

- **Key** = `game` field on each game dict, stripped. Empty / None → bucket `""` rendered last with header label `"(CHƯA NHÓM)"`.
- **Group order** = order of first appearance in `self._order`. Ungrouped bucket always last.
- **Within group** = `self._order` slice for that key.

## Interaction

- **Selection:** `_on_select` reacts only when current item has `kind == "game"`. Group headers are not selectable for editing but track `self._focused_group` (last clicked group key).
- **Expand/collapse:** clicking the chevron or the group row toggles. State written to `self._collapsed` and persisted.
- **`+ MỚI` (top-level):** pre-fills `game` field on the new entry with `self._focused_group` if a group was last touched, otherwise empty (lands in `(CHƯA NHÓM)`).
- **Group header `+`:** same as add-new, scoped to that group's key.
- **Group header `⋮` menu:**
  - `Đổi tên nhóm…` — `QInputDialog`, rewrites `game` on all children of this group. Note: themes (`game_themes.json`) reference these keys for hero art; rename does *not* touch themes. (Out of scope; show hint in dialog.)
  - `Thu gọn nhóm khác` — collapse every other group.
  - `Thêm vào nhóm này` — same as `+`.
- **Edit form:** unchanged. `_field_game` continues to be a free-text field; editing it moves the game between groups on next refresh.

## Visual / QSS

New objectNames added to `resources/qss/styles.qss`, palette consistent with existing manager styling (`#d8ff3a` accent on `#0a0a0e` rail):

- `QTreeWidget#MgrTree` — replaces `QListWidget#MgrList` rules
- `QFrame#MgrGroupHeader` (+ `[focused="true"]` property) — group row container
- `QLabel#MgrGroupChevron`, `QLabel#MgrGroupName`, `QLabel#MgrGroupCount`
- `QPushButton#MgrGroupAction` — hover-revealed `+` and `⋮`
- `QFrame#MgrChild` (+ `[selected="true"]`) — child row container
- `QLabel#MgrChildIndex`, `QLabel#MgrChildName`, `QLabel#MgrPartsChip`

Selection highlight on the child row matches the existing list selection (left chartreuse bar + tinted background).

## Migration

- Delete inline `[N parts: ...]` and `[No download parts]` annotation from `_refresh_list` — chip widget replaces it.
- Tooltip with full URL list moves from `QListWidgetItem.setToolTip` to the `_GameRow.setToolTip`.
- All Vietnamese strings live inline (consistent with rest of Manager tab; no `strings_vi.py` constants for this view).

## Out of scope

- Drag-to-reorder games between groups
- Multi-select / bulk actions
- Search/filter in the inventory
- Renaming the corresponding key in `game_themes.json` when a group is renamed
