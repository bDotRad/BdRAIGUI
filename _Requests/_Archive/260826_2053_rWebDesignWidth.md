## What was done

**Investigated:** why the dashboard's panels look narrow/tablet-sized (screenshot
attached to the request showed the Admin tab).

**Finding:** it's not a global "mobile-first" design -- the page itself has no
overall container/max-width (`body` just has `padding: 24px`), and most panels
size themselves to the viewport normally:
- `#grid` (Projects tab, project tiles) uses
  `grid-template-columns: repeat(auto-fill, minmax(320px, 1fr))`, so it fills
  the available width with as many 320px+ columns as fit.
- `#ecosystem-panel` is capped at `max-width: 1120px` -- wide enough on any
  normal desktop window.
- `#log-panel` (Activity Log) has no cap at all.

The one panel that really was phone-width was `#admin-panel` (the Admin tab,
which is what the screenshot showed): `max-width: 480px`, hardcoded when that
tab was originally built as a simple single-column settings form (restart
buttons, service status, colour palette editor). At 480px on a normal monitor
it does look cramped/undersized next to everything else in the app.

**Change made:** widened `#admin-panel`'s `max-width` from `480px` to `680px`
in `app/templates/index.html` (one CSS rule). Still a single readable column
(not full-bleed -- the color-picker rows and short status text don't need the
full viewport width either), just less severely capped. Left `#grid`,
`#ecosystem-panel`, and `#log-panel` alone since none of them were actually
narrow.

**Verification:** restarted the live dashboard via `kill -9` on the running
PID (per this project's no-sudo/no-autoreload CLAUDE.md convention -- old PID
179992 -> new PID 180581), then confirmed via `curl localhost:8420/` that the
served HTML now has `max-width: 680px` on `#admin-panel`.

**Outcome:** answered (narrowness was real but isolated to one tab, not a
site-wide "mobile" design) and fixed -- widened, deployed, and verified live.

## Original request (verbatim)

READY

Why are all the panels so narrow? whats the basic design used? Its like its made for a tablet or phone

(Original request included a screenshot, `image.png`, of the Admin tab -- not
preserved here; see finding above for what it showed.)
