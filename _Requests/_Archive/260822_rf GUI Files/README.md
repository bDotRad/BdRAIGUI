# Claude Code dashboard + scheduler

Two independent processes:

- **`dashboard.py`** — the web UI. Shows every project, which one is
  currently active, what phase it's in, and lets you tick projects in/out
  of the rotation. It never touches tmux or Claude directly — purely
  reads state and writes your selection.
- **`scheduler.py`** — the always-on daemon that actually does the work:
  round-robins through whichever projects are ticked, checks each one's
  `requests/` folder, wakes/runs Claude Code when there's something to do,
  and hibernates (kills the tmux session) once a project's gone quiet.

They talk to each other only through two small JSON files in
`~/claude-dashboard/state/` — `selected_projects.json` (dashboard writes,
scheduler reads) and `scheduler_state.json` (scheduler writes, dashboard
reads). Neither process needs the other running to stay up; if the
dashboard crashes, the scheduler keeps working — you just can't see or
change the rotation until it's back.

## Scheduler behaviour

For the currently active project in the pool:

1. Check `requests/` — this is a cheap directory listing, no Claude
   session needed.
2. **Files found:** start the project's tmux/Claude Code session if it
   isn't already running, send it a prompt to process the requests, wait
   a few seconds, check again. Repeats until the folder is empty.
3. **Folder empty:**
   - If the session had been running, wait 30s and check once more.
     Still empty → hibernate (kill the tmux session) and move to the
     next project in the pool.
   - If nothing was running to begin with, just move on immediately —
     no point starting Claude to confirm there's nothing to do.

This means a project that's genuinely quiet costs nothing — no session
gets spun up just to check it. Sessions only start when there's real
work, and get torn down again once that work is done.

Tmux sessions are expected to follow `proj-<project-name>` — change
`TMUX_SESSION_PREFIX` in both `dashboard.py` and `scheduler.py` if yours
differs. Same for the `claude` launch command if your binary/alias is
named differently.

## Setup on the Pi

```bash
cd ~
# copy this folder to the Pi (scp/SFTP), then:
cd claude-dashboard
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Try it manually first, in two terminals:

```bash
# terminal 1
python3 dashboard.py
# terminal 2
python3 scheduler.py
```

Open `http://<pi-ip>:8420`, tick a project into the rotation, and drop a
file in its `requests/` folder to watch the scheduler pick it up.

### Run both permanently

Edit `User`, `WorkingDirectory`, and the `PROJECTS_DIR`/`STATE_DIR` paths
in **both** `.service` files if your username or paths differ from
`brad` / `/home/brad/...`, then:

```bash
sudo cp claude-dashboard.service claude-scheduler.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now claude-dashboard claude-scheduler
```

Check they're both up:

```bash
systemctl status claude-dashboard claude-scheduler
```

## status.json (optional, for the "current task" text)

The dashboard shows a `current_task` line per project if your Claude Code
wrapper writes one to `~/projects/<name>/.claude-status/status.json`:

```json
{ "current_task": "Implementing user auth flow", "last_active": "2026-08-23T10:15:00Z" }
```

Not required — everything else (active project, phase, pending count,
last commit) comes from the scheduler and git directly.

## Notes

- Port `8420` is arbitrary — change it at the bottom of `dashboard.py` if
  it clashes with something else.
- `EMPTY_GRACE_SECONDS` (30s) and `POLL_WHILE_PROCESSING` (5s) in
  `scheduler.py` are the two timing knobs if you want it snappier or more
  relaxed.
- With just one project ticked, the scheduler still applies the same
  logic to it — it'll hibernate that session after two empty checks and
  simply loop back to itself, so it only ever restarts when there's
  actually new work.
