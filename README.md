# BdRAIGUI

Web dashboard + round-robin scheduler for the Claude Code projects under
`~/projects` on this Pi. Built from the example dropped in
`_Requests/rf GUI Files/` (see `_Requests/_Archive/` for the processed
request writeup).

Two independent processes, talking to each other only through JSON files
in `state/`:

- **`app/dashboard.py`** — the web UI (Flask). Shows every project, which
  one is currently active, what phase it's in, a rolling activity log,
  and lets you tick projects in/out of the rotation. Also surfaces any
  pending SQL a project has left for you to run by hand (see below).
  Never touches tmux or Claude directly — purely reads state and writes
  your rotation selection.
- **`app/scheduler.py`** — the always-on daemon that does the actual
  work: round-robins through whichever projects are ticked, checks each
  one's `_Requests/` folder for READY items, wakes/runs Claude Code in a
  tmux session when there's something to do, and hibernates (kills the
  tmux session) once a project's gone quiet. Appends events to
  `state/activity_log.jsonl` as it does so.

`app/common.py` holds the logic both processes share (project listing,
request scanning, state file I/O) so they can't drift out of sync on
what counts as "pending".

## Conventions this implements

- **Request intake**: `_Requests/<item>` per project, gated by a
  first-line `READY`/`NOT READY` marker, `x`-prefix to ignore, `_`-prefix
  reserved for archive/meta folders (`_Archive`, `_Archived`, ...). See
  `_Instructions/Requests.md` for the full spec. `common.scan_requests()`
  is the implementation — it's what both the dashboard's pending badge
  and the scheduler's wake trigger read from, so they always agree.
- **Orchestration context**: `_Instructions/BdRAIGUI.md` is the doc meant
  to be copied into *other* projects' instructions so their Claude Code
  sessions understand they're running under this scheduler (why they get
  woken/killed, `.claude-status/status.json`, SQL output convention).
- **Status line** (optional, per project): a project can write
  `.claude-status/status.json` with `{"current_task": "...",
  "last_active": "<ISO8601>"}` to show a human-readable task line on its
  card.
- **SQL output** (optional, per project): if a Claude session working on
  a project needs a human to run some SQL by hand (e.g. in the Supabase
  SQL editor), it can write the statement(s) to
  `.claude-status/sql_output.txt` (or `.sql`). The project's card then
  shows a purple **SQL** badge; clicking it opens a read-only textarea
  with a Copy button and a Clear button (deletes the file once you've
  run it).
- **Creating a request from the UI**: each card has a **+ Request**
  button — type the request, optionally attach files, and submit. With
  no attachments it writes `_Requests/rN.md`; with attachments it makes
  `_Requests/rN/` containing `request.md` plus the files. Numbering
  auto-increments per project. Meant as the first step toward dropping
  requests in remotely (e.g. over Tailscale) without opening a terminal.

## Setup

```bash
cd ~/projects/_BdRAIGUI
python3 -m venv venv
source venv/bin/activate
pip install -r app/requirements.txt
```

Try it manually first, in two terminals:

```bash
# terminal 1
source venv/bin/activate && python3 app/dashboard.py
# terminal 2
source venv/bin/activate && python3 app/scheduler.py
```

Open `http://<pi-ip>:8420`, tick a project into the rotation, and drop a
`READY`-marked item in its `_Requests/` folder to watch the scheduler
pick it up.

### Run both permanently

Service files in `systemd/` are already pointed at `/home/bdr/...` and
user `bdr`, matching this machine. Install once the venv above exists:

```bash
sudo cp systemd/bdraigui-dashboard.service systemd/bdraigui-scheduler.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now bdraigui-dashboard bdraigui-scheduler
```

Check they're both up:

```bash
systemctl status bdraigui-dashboard bdraigui-scheduler
```

## Notes

- State lives in `./state/` (gitignored) — `selected_projects.json`
  (dashboard writes, scheduler reads), `scheduler_state.json` (scheduler
  writes, dashboard reads), `activity_log.jsonl` (scheduler appends,
  dashboard reads, capped to the last ~500 lines).
- Port `8420` is arbitrary — change it at the bottom of `dashboard.py` if
  it clashes with something else.
- `EMPTY_GRACE_SECONDS` (30s) and `POLL_WHILE_PROCESSING` (5s) in
  `scheduler.py` are the two timing knobs if you want it snappier or more
  relaxed.
- `CLAUDE_LAUNCH_CMD` defaults to whatever `claude` resolves to on
  `PATH` at import time (falls back to the bare string `"claude"`).
  Systemd's `PATH` is minimal and won't see `~/.local/bin`, so the
  scheduler service file pins it explicitly:
  `Environment=CLAUDE_LAUNCH_CMD=/home/bdr/.local/bin/claude`. Update
  that line if `which claude` ever resolves somewhere else.
- With just one project ticked, the scheduler still applies the same
  logic to it — it'll hibernate that session after two empty checks and
  simply loop back to itself, so it only ever restarts when there's
  actually new work.
