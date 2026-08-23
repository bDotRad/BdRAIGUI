## What was done

Two related changes to the request-intake convention and its web UI:

**1. Title-based request filenames.** `_Requests/` items are now named
`r<Title>.md` (or `r<Title>/` for folder requests), where `<Title>` is a
short human-readable description instead of a sequential number.

- `app/common.py`: replaced `_next_request_number()`/`_REQUEST_NUM_RE`
  with `sanitize_title()` (strips filesystem-illegal characters, collapses
  whitespace) and `request_title()` (recovers the title from a filename by
  stripping the leading `r`). `create_request_file()` and
  `create_request_folder()` now take a `title` argument and build the
  filename from it via `_unique_request_name()`, which appends a numeric
  suffix (` 2`, ` 3`, ...) only on an actual collision.
- `app/dashboard.py`: `POST /api/requests/<project>` now requires a
  `title` form field (400 if missing), same as it already required
  `content`.
- `app/templates/index.html`: the "+ Request" modal has a new Title input
  above the content textarea; `submitRequest()` sends it and refuses to
  submit without one.
- `_Instructions/Requests.md`: rewrote "How to add something" and the
  other `rNNN`-era references (split-file example, `x`-prefix example,
  "scan rNNN" trigger, archive-collision rationale) to describe and use
  title-based names throughout.

**2. Per-project request status list.** New `GET
/api/requests/<project>/list` endpoint (`common.list_requests()`) returns
each outstanding request's recovered title plus a display status:
`Ready`, `Not Ready`, `Waiting Response`, or `Processing` -- the last one
shown for `READY` items specifically while this project is the
scheduler's active project *and* its phase is `processing` (i.e. a
session is actively working through them right now), so it naturally
reverts to `Ready` once that pass ends. Rendered as a Title/Status table
in a new "Requests" panel on the per-project detail page
(`app/templates/project.html`), alongside the existing Description and
Claude agent files panels.

Refactored `common._is_ready()` into a new `_request_marker()` (returns
the raw marker string, defaulting to `NOT READY`) so both the existing
ready/not-ready scan and the new status list share one marker-reading
implementation instead of two.

**Outcome:** implemented and working (verified `create_request_file`,
`request_title`, and `list_requests` directly against a temp project
dir). Not yet live on the dashboard -- per `CLAUDE.md`, Flask runs
without autoreload, so this needs the usual restart step:

```
sudo systemctl restart bdraigui-dashboard
```

No `sudo` available to this session; Brad needs to run that (or the
service will pick it up on its own next restart) before the new Title
field / status list actually appear at http://<pi-ip>:8420.

---

READY

For requests, ask for a title - this will become the file name.
If a file is just dropped into the Request folder, the file name is the Request Title (minus the r )

On the web interface, show a list of items with the status next to them.
ie
Title                              Status
Request status list                Processing
Logo resize                        Ready
Background colour                  Ready
Page title size                    Waiting Response
Font colour                        Not Ready



Update any claude docs you need
