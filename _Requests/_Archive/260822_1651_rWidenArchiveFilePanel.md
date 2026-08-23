# 260822 — Archive browser: widen the file-list column, stop the horizontal scrollbar

## Done

The archive browser modal's file list (`#archive-list` in
`app/templates/index.html`, last sized in
[[260822_1614_rArchivePanelLayout]]) was a fixed `flex: 0 0 260px`
column. Filenames in this archive are long (e.g.
`260822_1633_rArchivePanelRestart.md`) and the list items had no
truncation, so long names forced the column to grow a horizontal
scrollbar instead of wrapping or eliding — matching the attached
screenshot ("Too Narrow" callout pointing at that scrollbar).

Fixed in `app/templates/index.html`:

- `#archive-list` widened from `flex: 0 0 260px; min-width: 200px` to
  `flex: 0 0 420px; min-width: 320px`, and `overflow-x: hidden` added
  so it can no longer grow a horizontal scrollbar of its own.
- `.entry-name` given `min-width: 0; overflow: hidden; text-overflow:
  ellipsis; white-space: nowrap` — the real bug underneath the visual
  one: a flex child's default `min-width: auto` refuses to shrink
  below its content width, which is what was forcing the row (and
  therefore the list) wider than its container. Now a name too long
  even for the widened column ellipsizes instead of pushing a
  scrollbar back in.
- `#archive-modal`'s `max-width: 1100px` was already wide enough to
  absorb the extra list width without cramping the text-viewer panel
  on the right.

**Live dashboard needs a restart to pick this up** — no passwordless
sudo in this session, and the dashboard looked actively in use
(requests logged seconds before this pass), so per CLAUDE.md that's
Brad's call rather than a `kill -9` done mid-session:

```
sudo systemctl restart bdraigui-dashboard
```

## Requested

READY

Panel is too narrow - see attached pic

(attached: screenshot of the archive browser modal with a "Too Narrow"
callout pointing at a horizontal scrollbar under the file list)
