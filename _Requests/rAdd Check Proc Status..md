WAITING RESPONSE

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
