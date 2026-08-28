# Workspace tab — sidebar of projects, full-width console/archive/request

**Asked:** Brad wanted the dashboard to use page space better ("feels like a
combo of mobile and desktop") and, on top of the existing Projects-as-tiles
view, a page with tabs down the side for each project where console, archive
and new-request use the whole page instead of a small popup.

**Clarified with Brad (3 questions):**
- Placement: **new top-level tab** ("Workspace") next to Projects/Activity
  Log/Admin/…; the tiles view on the Projects tab is untouched.
- Per-project pane: **sub-tabs** — Requests | Console | Archive | + New
  Request — each filling the full content area.
- Modals: **left as-is on the tiles view**; the separate `/project/<name>`
  page is effectively retired — the tile *name* now opens the Workspace pane
  for that project (the `/project/<name>` route/template stays as a fallback
  URL, linked from the pane header as "detail page ↗").

**What changed — `app/templates/index.html` only** (no `dashboard.py` /
`common.py` changes; every endpoint the pane needs already existed):

- New **Workspace** tab button + `#tab-panel-workspace`.
  - Left rail (`#workspace-sidebar`, 220px) lists every project, active
    group then an "Inactive" group, each row with a phase dot
    (green = scheduler-active, amber = has a Waiting Response request,
    grey = idle) and a count badge of Ready/Processing requests. Rebuilt
    from `/api/status` on the existing 5s poll.
  - Selecting a project shows a full-width pane with a header
    (name + "detail page ↗" link to `/project/<name>`) and four sub-tabs:
    - **Requests** — table (title / status / Mark Ready·Not Ready·Shelve),
      inline textarea editor on row click, plus a Shelved list with
      Unshelve/Delete. Uses `/api/requests/<p>/list`, `/content`,
      `/ready`, `/not-ready`, `/shelve`, `/shelved/*`.
    - **Console** — full-height live pane, 3s poll while this sub-tab is
      showing, reply input (Enter to send), Expand agent (ctrl+o), Refresh.
      Uses `/api/console/<p>` + `/send` + `/key`.
    - **Archive** — full-height list + viewer with breadcrumbs, text and
      image preview. Uses `/api/archive/<p>` + `/file` + `/raw`.
    - **+ New Request** — full-page form (title, content, READY checkbox,
      file picker + paste-anywhere screenshot capture), posts to
      `/api/requests/<p>`, then drops back to the Requests sub-tab.
  - Selected project and sub-tab persist in `localStorage`
    (`bdrdev-ws-project`, `bdrdev-ws-subtab`); the tab itself already
    persisted via `bdrdev-tab`. Console polling is stopped whenever you
    leave the Workspace tab or the Console sub-tab.
- Tiles view: the project-name link keeps its `href="/project/<name>"`
  (so middle-click / open-in-new-tab still works) but `onclick` now jumps
  to the Workspace pane for that project instead.

**Outcome:** deployed. `app/templates/index.html` edited; dashboard
restarted via `POST /api/admin/restart` (the Admin-tab mechanism —
SIGKILL self-restart, ~1s outage) and verified live: `GET /` returns 200
and serves the Workspace tab; the full page's inline `<script>` parses
clean; `/api/status`, `/api/archive/<p>`, `/api/console/<p>` all respond
in the shape the new code expects. No DB/schema change.

---

## Original request (`rPage Types.md`)

```
READY

I want to better use the space on the page. It feels like this website is a combo of mobile and desktop.

Updates.
I like hte ideas of the Projects as Tiles, but Id also like a page with tabs down the side for each project, and then utilise the entire page to show console, archive, and new request is full page not a small popup.
```
