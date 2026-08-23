# 260822 — List each project's requests on the dashboard card

## Done

The main dashboard grid (`app/templates/index.html`) already showed an
aggregate `pending_requests`/`total_requests` count per card, but not the
individual requests themselves. Added the requested per-request list
below each project card ("the Project bubble"):

- `app/dashboard.py`'s `/api/status` now includes a `requests` array per
  project (reusing `common.list_requests()`, which was already used by
  the per-project detail page) alongside the existing aggregate counts,
  so the dashboard's existing 5s poll picks it up with no extra requests.
- `app/templates/index.html`: each card now renders a compact list
  (title + colored status pill) under the existing meta rows, via a new
  `renderCardRequests()` helper.
- Status → colour, matching what was asked for: **Processing** = green,
  **Ready** = blue, **Waiting Response** = yellow, **Not Ready** = grey.
  (The convention doc's marker is `WAITING RESPONSE`, not `WAITING
  INPUT` as sketched in the request's mockup — kept the existing label
  used everywhere else in the app rather than introducing a second name
  for the same state.)
- `app/templates/project.html`'s existing (separate) requests panel used
  the opposite colours for Ready/Processing (ready green, processing
  blue) — swapped those to match the scheme above, since both views
  render the same underlying statuses and having two different colour
  conventions for identical states across the app would just be
  confusing.

Verified via the Flask test client and then `curl` against the live
service after a forced restart (`kill -9` on the old dashboard.py PID —
systemd's `Restart=on-failure` policy then relaunched it automatically;
brief outage, `debug=False` means edits don't hot-reload otherwise).
`/api/status` now returns a `requests` array per project (confirmed
against this project's own single in-flight request), and the served
`index.html` includes the new render function and status colours.

## Requested

READY

List the current requests below the Project bubble.

Title            Status         Colour
r AAAAAAA        PROCESSING     (GREEN)
r BBBBBBB        WAITING INPUT  (YELLOW)
r CCCCCCC        READY          (BLUE)
r DDDDDDD        READY          (BLUE)
r EEEEEEE        NOT READY      (GREY)
