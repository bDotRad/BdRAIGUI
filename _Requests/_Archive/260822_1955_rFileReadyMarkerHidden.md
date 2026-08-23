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

---

## Original request

READY

I made a file in another project called test. I clicked Make Ready. But when I click on it to view, it doesn't have READY on the top line. so how does it know its ready?
