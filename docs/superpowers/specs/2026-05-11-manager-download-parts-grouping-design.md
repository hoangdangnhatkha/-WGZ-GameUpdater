# Manager Tab Download Parts Grouping Design

## Overview
Enhance the Manager tab (Tab 4) to show download parts information directly in the games list view, allowing users to see which download parts belong to which game without entering edit mode.

## Current State
- Manager tab displays games in a list (`_GamesEditor._build_left()`)
- Each game shows only basic info: ID, name
- To view download parts (URLs), user must select a game and enter edit mode
- Download parts are stored in each game's `urls` field

## Problem
Users cannot quickly see which download parts belong to which game when browsing multiple games. They must enter edit mode for each game individually to see its download parts.

## Solution
Enhance the game list to show download parts summary for each game, with optional expandable details.

### Design Details

#### 1. Enhanced Game List Item
Modify `_GamesEditor._refresh_list()` to show download parts information:

```python
# Current:
item = QListWidgetItem(f"  {i:02d}    {name}")

# Enhanced:
download_count = len(game.get("urls", []))
if download_count > 0:
    # Show count and first few URLs as preview
    preview_urls = game.get("urls", [])[:2]  # Show first 2 URLs
    preview_text = ", ".join([url.split("/")[-1] for url in preview_urls])
    if len(game.get("urls", [])) > 2:
        preview_text += f" (+{len(game['urls']) - 2} more)"
    item_text = f"  {i:02d}    {name}  [{download_count} parts: {preview_text}]"
else:
    item_text = f"  {i:02d}    {name}  [No download parts]"
item = QListWidgetItem(item_text)
```

#### 2. Expandable Rows (Optional Enhancement)
Implement expandable rows using QTreeWidget or custom widget to show detailed download parts when expanded:

- Collapsed: Shows game name + download parts count
- Expanded: Shows list of download parts with:
  - URL (truncated)
  - File type (from extension)
  - Size info (if available from metadata)
  - Order/index

#### 3. Visual Indicators
Add visual cues for download parts status:
- Icon indicating file type (ZIP, RAR, EXE)
- Color coding for different part types
- Tooltip showing full URL on hover

#### 4. Data Flow
No changes needed to data storage - download parts remain in each game's `urls` field
Only presentation layer is enhanced

## Benefits
1. **Quick Overview**: See download parts for all games at a glance
2. **Reduced Clicks**: No need to enter edit mode just to see what parts a game has
3. **Better Organization**: Download parts are clearly grouped by their parent game
4. **Improved Workflow**: Faster identification of games with specific download part configurations

## Implementation Considerations
1. **Performance**: Limit preview to first 2-3 URLs to avoid long list items
2. **Usability**: Ensure list items remain readable with added information
3. **Consistency**: Match existing UI styling and patterns
4. **Fallback**: Gracefully handle games with no download parts

## Related Files
- `wgz_updater/features/manager/view.py` - `_GamesEditor` class
- Specifically: `_refresh_list()` method and `_populate_form()` for potential enhancements

## Testing
1. Verify list shows correct download parts count for each game
2. Check that preview text is meaningful and not overly long
3. Ensure list remains usable and readable with added information
4. Test with games having 0, 1, 2, and many download parts
5. Verify existing edit functionality still works correctly