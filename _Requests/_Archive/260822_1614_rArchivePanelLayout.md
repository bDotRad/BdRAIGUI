# 260822 — Archive viewer: text panel on the right, not stacked below

## Done

The archive browser modal (`app/templates/index.html`, added in
[[260822_1535_rArchiveBrowse]]) stacked the file list on top and the text
viewer below it inside one narrow (640px) column, so the viewer only got
a small sliver of vertical space once a file was open.

Reworked the layout:

- `#archive-modal` widened from `max-width: 640px` to `1100px`.
- New `#archive-body` flex row wraps the list and the viewer side by
  side: `#archive-list` is now a fixed 260px-wide left column
  (`flex: 0 0 260px`, own scrollbar, right border as a divider),
  `#archive-view` is a `flex: 1` panel on the right.
- The right panel now always occupies its space — it shows a "Select a
  file to view its contents." placeholder before anything's picked, and
  swaps to the `<textarea>` once `viewArchiveFile()` loads content — so
  the list stays visible and clickable while browsing files instead of
  being replaced by the viewer.
- No JS logic changes; `loadArchivePath`/`viewArchiveFile` already
  toggled the `.open` class on `#archive-view`, which now just
  controls which of (placeholder / textarea) shows rather than
  hiding/showing the whole panel.

Verified via Flask test client that `/` renders with the new
`#archive-body`/`#archive-view-placeholder` markup and the widened
modal. **Live dashboard needs a restart to pick this up** — no
passwordless sudo in this session, so per CLAUDE.md that's Brad's call:

```
sudo systemctl restart bdraigui-dashboard
```

## Requested

READY

For the archive review can you make the text window appear on the right in a panel so i can see more.
