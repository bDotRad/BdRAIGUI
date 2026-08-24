## What was done

This request restates the same ask already fixed and archived earlier
today in `260824_0751_ConsoleSnapshotOnNotReady.md` (committed `3d99357`,
archive commit `79daac8`): flicking a request from READY back to NOT
READY was throwing away the live Console pane content, which often held
useful in-progress context.

Checked that the fix is still in place and live:

- `common.set_request_not_ready()` still takes a `console_snapshot` arg
  and, when non-blank, appends it into the request's own `.md` body
  under a dated `Console snapshot when marked Not Ready (...)` header,
  fenced as a code block, before flipping the marker to `NOT READY`.
- `dashboard.api_request_not_ready()` still grabs `tmux_capture()` of the
  project's console (if the session is alive) and passes it through.
- Confirmed via `curl http://127.0.0.1:8420/api/status` that the running
  `bdraigui-dashboard` process (started 07:48, after this code landed)
  is serving current code, and neither function was touched by the
  separate unrelated changes currently uncommitted in the working tree
  (those implement the still-`NOT READY` "Independent Claude tab"
  request and were left alone).

This request's body does float one implementation variant beyond what
was built -- "maybe make a folder and combine the .md and the claude
log" (a separate log file alongside the request, instead of appending
the snapshot as a fenced block inside the same `.md`). The core ask --
"save into a file in the request" -- is satisfied by the existing
append-in-place approach, so treating this as the same request rather
than a distinct follow-up. If Brad specifically wants the
separate-file/folder layout instead, that's a distinct, smaller ask he
can drop back into `_Requests/`.

**Outcome:** no code change needed -- already fixed by the earlier pass
today. Duplicate request archived.

## Original request

READY

When flicking to NOT READY some of the context is lost from the Claude console.
Need to sale the claude convo and save into a file in the request...maybe make a folder and combine the .md and the claude log
