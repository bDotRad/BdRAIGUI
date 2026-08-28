# Processing tab — "button to see where request processing is at"

**Asked:** a way to click a button and get an update on where the
request-processing sessions are, because "they seem to get stuck".

**Done** (built + shipped in `2694755`, restarted by Brad 19:16 and run
live for a few minutes):

- New **Processing** tab (2nd tab). One card per project session
  (`proj-<name>` tmux), colour-coded: green `working` / amber
  `waiting_input` (parked on a permission or plan prompt) / grey `idle`
  / red `stuck?` (still has READY requests but a live session that
  isn't working). Tab label goes red when any project is `stuck`.
- Per card: READY-vs-total request count + each request's marker, the
  scheduler phase for that project, and the last ~40 lines of the pane.
- Below the cards: the last 30 scheduler activity-log events.
- Auto-refreshes every 4s while the tab is open. Backed by
  `/api/proc-status`; pane reader is `common.list_project_sessions()`.
  README updated.

**Outcome:** Brad reviewed it live, first flipped to READY with no
notes (bounced back to WAITING RESPONSE for clarification), then
confirmed: **"Itll do for now."** Archived as-is, no further changes.

---

## Original request (verbatim)

```
READY

Itll do for now.

## You flipped this to READY with no notes — what do you want changed? (Claude, 2026-08-28)

I picked up the session. Before flipping this, you restarted the
dashboard (19:16) and had it running the new code for ~3 min. It's live
and working:

- The **Processing** tab is present (2nd tab) and `/api/proc-status`
  returns sensible data — one card per project session, colour badge
  (working / waiting input / idle / stuck?), ready-vs-open request
  counts, scheduler phase, the pane tail, and the last 30 activity-log
  events below. Auto-refreshes every 4s. Tab label turns red when a
  project is flagged `stuck`.
- Right now it correctly shows BdRDev = `working` (this session), the
  other projects with no live session, `_IndependentClaude` idle and
  "not in rotation", nothing stuck.

So the feature itself checks out. But you marked this READY instead of
archiving, which the request says means "notes on what to change" — and
there are no notes. I can't guess what you want, so I've set this back
to **WAITING RESPONSE**.

**Tell me one of:**
- "Archive it, looks fine" — I'll archive it next pass.
- What's wrong / missing / what you want different on the Processing
  tab (layout, extra info, different stuck detection, a manual
  "kick this session" button, etc.).
- If you flipped it to READY by accident, just say so.

---

## Built — needs a dashboard restart to see it (Claude, 2026-08-28)

New **Processing** tab (second tab, after Projects). Click it for a live
view of where request processing is right now:

- One card per project session (`proj-<name>` tmux), colour-coded:
  - **green** — `working`: Claude Code's "esc to interrupt" indicator is
    up, or the pane produced new output between two captures 1.5s apart.
  - **amber** — `waiting_input`: the pane is parked on a permission /
    plan prompt (numbered "1. Yes" list, "Do you want…", etc.).
  - **grey** — `idle`: session alive, nothing happening.
  - **red / "stuck?"** — the project still has READY requests *and* a
    live session that isn't working. This is the "they get stuck" case:
    a session hit an interactive prompt and stopped without setting its
    request to `WAITING RESPONSE`. The tab label also goes red.
- Per card: READY vs total request count, each request's marker, the
  scheduler's phase for that project, and the last ~40 transcript lines
  of the pane so you can see what it's sitting on.
- Below the cards: the last 30 scheduler activity-log events.

Auto-refreshes every 4s while the tab is open. Backed by a new
`/api/proc-status`; the pane-reading helper is
`common.list_project_sessions()`. README updated.

Committed + pushed (`2694755`).

@@@ --- Action --- @@@

1. Pick up the new tab (and the Fleet/Ecosystem 2 changes from
   `rEditing Tables`, same restart).

"Restart the dashboard so the new template + routes load. Either click
 Admin -> System -> 'Restart service', or on this dev box:"
sudo systemctl restart bdrdev-dashboard

"Then open the Processing tab and check it shows something sensible."

@@@ ------------- @@@

Once you've looked: archive this if it's what you wanted, or flip to
`READY` with notes on what to change.

---

Add something so I can click a button to get an update of wehre the processsing files are at. they seem to get stuck
```
