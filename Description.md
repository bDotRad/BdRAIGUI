# BdRAIGUI

Web dashboard + round-robin scheduler that runs Claude Code across every
project under `~/projects` on this Pi (this project included).

- **Dashboard** (`app/dashboard.py`, Flask, port 8420) — shows every
  project's status, lets you tick projects in/out of the rotation, and
  is where requests get dropped in via the **+ Request** button on each
  project's card.
- **Scheduler** (`app/scheduler.py`) — the always-on daemon that
  actually does the work: watches each rotated-in project's
  `_Requests/` folder, wakes a Claude Code session (in tmux) when
  there's a `READY` item, and hibernates it again once it's quiet.

Drop a request in a project's `_Requests/` folder (or use the dashboard's
**+ Request** button), tick the project into rotation, and the scheduler
picks it up on its own.

See `README.md` for setup and architecture details. `CLAUDE.md` is a
separate file, written for the Claude Code sessions the scheduler wakes
in this project -- not this description.
