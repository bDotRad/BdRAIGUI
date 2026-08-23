# rUpdate Project Tile — simplify the project card layout

**Asked:** three changes to each project tile in `app/templates/index.html`
(see `260822_rf Update Project Tile/image.png` for the annotated
screenshot): (1) replace the separate "In rotation" checkbox + "ACTIVE"
pill badge with a single checkbox top-right, labeled "Active" in blue
when checked / "Inactive" in grey when unchecked; (2) remove the
"No current task" line, the "Last active" / pending-count row, and the
last-commit row; (3) move the Files / Archive / Console / + Request
links above the per-project request list.

**Done:** in `app/templates/index.html`:
- `renderGrid()` — replaced the `.toggle-row` "In rotation" checkbox and
  the `activeBadge` pill with one `.active-toggle` checkbox+label in the
  card head (`Active`/`Inactive`, still wired to the same
  `toggleRotation()` call, only the label/color changed). The `.card.active`
  border highlight (driven by `is_active`, the scheduler's current
  project) was left as-is — it's a separate signal from the rotation
  checkbox and wasn't called out for removal.
- Deleted the `task`, two `meta` rows (last-active/pending, last-commit/
  phase), and their now-dead CSS (`.task`, `.meta`, `.pending`,
  `.phase-tag`/`.phase-*`). Backend fields (`current_task`,
  `last_active_relative`, `last_commit`, `pending_requests`, `phase`)
  were left in `common.py`/`dashboard.py`'s API response — only the
  index-page rendering of them was removed, since nothing else in the
  UI depends on the fields being dropped from the payload.
- Moved `card-foot` (the four links) to right after `card-head`, before
  `renderCardRequests(p.requests)`.

**Outcome:** done. Verified by running the app under its `venv` on a
scratch port (8499, separate from the live service on 8420) and hitting
`/` and `/api/status` with curl — page loads 200, API payload shape
unchanged, JS template markup reviewed by hand for balanced tags. No
Python changes, so this doesn't need `sudo systemctl restart
bdraigui-dashboard` for backend correctness, but the live dashboard
still runs pre-edit `index.html` out of its process (Flask has no
autoreload here) — Brad needs to `sudo systemctl restart
bdraigui-dashboard` (or `kill -9` the worker pid, per CLAUDE.md) to see
this on the real page. Original request + screenshot moved wholesale to
`260822_rf Update Project Tile/`.

---

READY

1. instead of In Rotation and the Active just put one check box at the top right. Then if its clicked its Active in Blue. And if not checked says Inactive in Grey.
2. Remove
No Current Task
Last Active
Number Ready
the next line of what was processed
3. Put the Files, Archive, Console, +Request above the list of files
