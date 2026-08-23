## What was done

**Asked:** add a way to "shelve" a request — park it aside without
deleting or archiving it — into a new `_Shelved` folder, with the
ability to delete or unshelve it from the project's file-viewing page.

**Found:** already implemented (uncommitted) in the working tree when
this pass started:

- `app/common.py` — `SHELVED_SUBDIR = "_Shelved"`, plus
  `shelve_request()`, `list_shelved()`, `unshelve_request()`,
  `delete_shelved_request()`. Moves go through `_move_unique()`, which
  appends a numeric suffix on a name collision instead of overwriting.
- `app/dashboard.py` — three new routes: `POST
  /api/requests/<project>/shelve`, `GET
  /api/requests/<project>/shelved/list`, `POST
  /api/requests/<project>/shelved/unshelve`, `POST
  /api/requests/<project>/shelved/delete`. Each logs an activity-log
  event (`request_shelved`/`request_unshelved`/`request_shelved_deleted`).
- `app/templates/project.html` — new "Shelved" panel on the project
  page, listing shelved items with Unshelve/Delete buttons, plus a
  "Shelve" button added to each row of the existing requests table.
- `app/templates/index.html` — the three new event types added to
  `EVENT_LABELS` so they render sensibly in the activity log.

**Verified:** `py_compile` clean on all three `app/*.py` files. The
dashboard process (pid confirmed via `ps`) was already running this
code — file mtimes on `common.py`/`dashboard.py`/`templates/*.html`
predate the running process's start time, and `GET /api/admin/status`
reports `needs_restart: false`, so no restart was needed this pass.
Did a live round-trip against the running dashboard: created a throwaway
request file, `POST .../shelve` moved it into `_Requests/_Shelved/`,
`GET .../shelved/list` showed it, `POST .../unshelve` moved it back to
`_Requests/`, re-shelved it, then `POST .../shelved/delete` removed it
for good — confirmed via `ls` at each step. Cleaned up the empty
`_Shelved/` test directory afterward. Also loaded `/project/_BdRAIGUI`
live and confirmed the new "Shelved" panel and its JS render.

**Outcome:** feature was already fully implemented and working; nothing
left to fix. Committed and pushed as part of this pass, along with two
other locally-implemented-but-uncommitted fixes from earlier the same
day (restart-flag debounce, activity log DST fix) that were sitting in
the same uncommitted working tree.

---

## Original request (verbatim)

READY

Add a Shelf request. This puts it in another folder called _Shelved (you will need to add)
When viewing the files of a project, you can delete shelved requests, or unshelve them
