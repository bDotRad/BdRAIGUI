## What was done

Brad reported that moving a request from READY back to NOT READY threw
away whatever was in that project's Console pane, even though it often
held useful in-progress context from the live session.

Found that a prior, uncommitted pass had already implemented the fix in
the working tree (staged in git, never committed):

- `common.set_request_not_ready()` gained an optional `console_snapshot`
  argument. When given non-blank content, it's appended to the request
  body under a dated `Console snapshot when marked Not Ready (...)`
  header, fenced as a code block, before the marker line flips to
  `NOT READY`.
- `dashboard.api_request_not_ready()` now grabs a `tmux_capture()` of the
  project's console (if the session is alive) and passes it through.

Verified the change compiles (`python3 -m py_compile`) and confirmed via
`curl http://127.0.0.1:8420/api/status` that the live dashboard process
is already running this code (dashboard.py was restarted independently
of this session, picking up the file as it stood on disk). Committed
just this fix (`3d99357`) — the working tree also had unrelated,
unstaged changes across `common.py`/`dashboard.py`/`scheduler.py`/
`index.html` implementing the still-`NOT READY` "Independent Claude tab"
request; those were left alone rather than swept into this commit, since
that request isn't marked ready for processing.

No restart needed on my end — the running `bdraigui-dashboard` service
already reflects this code.

**Outcome:** fixed, committed, and pushed.

## Original request

READY

WHen I moved something from READY to NOT READY, the claude console info is lost. but most of the time it has some vital info. can it be saved into the request file/folder and then be attached later.
