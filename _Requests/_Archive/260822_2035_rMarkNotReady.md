## What was asked

This request bundled two things: a restated version of an earlier
already-answered question (why the edit dialog doesn't show `READY` on
its first line — see `260822_1955_rFileReadyMarkerHidden.md`), plus a
new, genuine ask on top: "If its stripped thats ok, just have the
ability to set back to Not Ready." Read as: the earlier explanation is
fine, but there's a real gap — once a request is marked `READY` there
was no UI way to flip it back to `NOT READY`.

## What was found

Confirmed the gap. `common.set_request_ready()` and the `/api/requests/
<project>/ready` endpoint existed, with a "Mark Ready" button shown in
the dashboard's per-project request list whenever a request's status
was "Not Ready" (`app/templates/index.html:577`). There was no
symmetric "Mark Not Ready" path in either direction — backend or UI.

## What changed

- `app/common.py`: added `set_request_not_ready(project, name)`,
  mirroring `set_request_ready()` — flips the item's first line to
  `NOT READY` in place, leaving the rest of the body untouched.
- `app/dashboard.py`: added `POST /api/requests/<project>/not-ready`,
  mirroring the existing `/ready` endpoint — resolves the request,
  calls `set_request_not_ready()`, logs a `request_marked_not_ready`
  event.
- `app/templates/index.html`: added `markRequestNotReady()` (mirrors
  `markRequestReady()`), and a "Mark Not Ready" button in
  `renderCardRequests()` shown whenever a request's status is "Ready"
  or "Processing" (both correspond to a `READY` marker on disk —
  "Processing" is just the display label used while the scheduler is
  actively mid-pass on that project). No button shown for "Waiting
  Response", consistent with the existing convention that that state is
  set by Claude and cleared by Brad answering and re-marking `READY`,
  not by a plain not-ready toggle.

## Outcome

Fixed and deployed. Restarted the dashboard via the existing
`POST /api/admin/restart` endpoint (self-`SIGKILL`, systemd relaunches
it — added in `260822_1857_rRequestEditable_rAdminTab.md`), then
verified live: `/api/admin/status` showed `needs_restart: false` after
restart, the served page includes the new `markRequestNotReady`
function, and `curl`-driven calls to both `/ready` and `/not-ready`
against this very request file correctly flipped its on-disk marker
line back and forth (`READY` → `NOT READY` → `READY`) before archiving.

---

## Original request

READY

I asked the following.
If its stripped thats ok, just have the ability to set back to Not Ready



## What was asked

Brad made a `test` request in another project, clicked "Mark Ready" in
the dashboard, then opened it to view/edit it -- the content shown
didn't have `READY` on the first line, so he asked how the system
knows it's ready if that's not visible.

## What was found

This is expected behavior, not a bug -- the "view" dialog deliberately
hides the marker line:

- `common.read_request_body()` (`app/common.py:438-450`) strips the
  marker line before returning content: `_, _, rest =
  text.partition("\n")` then returns `rest`. The `/api/requests/
  <project>/content` endpoint (`app/dashboard.py:140`) calls this, and
  the edit dialog's `openEditRequest()` (`app/templates/index.html:604`)
  loads from that endpoint. So the editor textarea only ever shows the
  body, never the `READY`/`NOT READY`/`WAITING RESPONSE` line.
- `write_request_body()` (`app/common.py:453-469`) is the save-side
  counterpart -- it re-reads whatever marker is currently on disk and
  re-prepends it untouched when saving the edited body. So editing and
  saving a request from the dashboard can't accidentally clobber or
  drop the marker.
- The marker is instead surfaced separately, as a status pill next to
  each request in the list (`req-mini-status` in
  `app/templates/index.html:143-147,566-578` -- "Ready" / "Not Ready" /
  "Processing" / "Waiting Response"), computed by
  `common.request_status()`. "Mark Ready" (`markRequestReady()`,
  `index.html:585`) hits `/api/requests/<project>/ready`, which calls
  `common.set_request_ready()` (`app/common.py:419-435`) -- this does
  rewrite the actual first line of the file on disk to `READY`, it's
  just that the dashboard's editor never displays that line back to
  you.

Verified by reading the request/response flow end-to-end; no code
change needed. If Brad wants the marker visible in the edit view too
(e.g. shown read-only above the textarea, separate from the editable
body), that'd be a small follow-up but wasn't asked for here.

## Outcome

Investigated, no code change needed -- answered as a how-it-works
question. Told Brad: the marker line *is* being set correctly on disk
by "Mark Ready" (and reflected in the status pill next to the request
in the list); the edit/view dialog just intentionally shows only the
body text, not the marker line, so you won't ever see `READY` inside
that textarea even when it's correctly set.

## Outcome

Investigated, no code change needed -- answered as a how-it-works
question. Told Brad: the marker line *is* being set correctly on disk
by "Mark Ready" (and reflected in the status pill next to the request
in the list); the edit/view dialog just intentionally shows only the
body text, not the marker line, so you won't ever see `READY` inside
that textarea even when it's correctly set.

---

## Original request

READY

I made a file in another project called test. I clicked Make Ready. But when I click on it to view, it doesn't have READY on the top line. so how does it know its ready?
