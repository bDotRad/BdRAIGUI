#!/usr/bin/env python3
"""
Claude Code round-robin scheduler.

Runs continuously, independent of the dashboard web app. Cycles through
whichever projects are currently selected (in ~/claude-dashboard/state/
selected_projects.json, written by the dashboard) and, for each:

  1. Check its requests/ folder (cheap — just a directory listing, no
     Claude session needed for this part).
  2. If there are pending files: make sure that project's tmux/Claude Code
     session is running (start it if not), send it a prompt to process
     the requests, then loop back and check again shortly after.
  3. If empty: wait 30s and check once more.
  4. If still empty on that second check: hibernate the session (kill the
     tmux session to free RAM) and move to the next selected project.
  5. If nothing was ever running for this project, just move on straight
     away — no point spawning Claude just to confirm there's nothing to do.

Writes its current state to ~/claude-dashboard/state/scheduler_state.json
so the dashboard can display it.

Run:
  python3 scheduler.py
(intended to run as a systemd service — see claude-scheduler.service)
"""

import json
import os
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

PROJECTS_DIR = Path(os.environ.get("PROJECTS_DIR", Path.home() / "projects"))
STATE_DIR = Path(os.environ.get("STATE_DIR", Path.home() / "claude-dashboard" / "state"))
STATE_DIR.mkdir(parents=True, exist_ok=True)

SELECTED_FILE = STATE_DIR / "selected_projects.json"
STATE_FILE = STATE_DIR / "scheduler_state.json"

TMUX_SESSION_PREFIX = "proj-"
CLAUDE_LAUNCH_CMD = "claude"
SCAN_PROMPT = "Check the requests folder for new or updated files and process them now."

EMPTY_GRACE_SECONDS = 30       # wait this long after first empty scan before rechecking
POLL_WHILE_PROCESSING = 5      # how long to wait between rechecks while there's work
IDLE_POOL_SLEEP = 5            # how long to sleep if no projects are selected at all
BETWEEN_PROJECT_PAUSE = 2      # brief pause when moving on from an already-quiet project


def load_selected():
    if not SELECTED_FILE.exists():
        return []
    try:
        return json.loads(SELECTED_FILE.read_text())
    except (json.JSONDecodeError, OSError):
        return []


def write_state(active_project, phase, pending=None, pool=None):
    STATE_FILE.write_text(json.dumps({
        "active_project": active_project,
        "phase": phase,
        "pending": pending,
        "rotation_pool": pool if pool is not None else load_selected(),
        "last_update": datetime.now(timezone.utc).isoformat(),
    }, indent=2))


def pending_count(project):
    req_dir = PROJECTS_DIR / project / "requests"
    if not req_dir.exists():
        return 0
    return sum(1 for f in req_dir.iterdir() if f.is_file())


def tmux_alive(project):
    session = f"{TMUX_SESSION_PREFIX}{project}"
    try:
        return subprocess.run(["tmux", "has-session", "-t", session], capture_output=True).returncode == 0
    except FileNotFoundError:
        return False


def spawn_session(project):
    session = f"{TMUX_SESSION_PREFIX}{project}"
    project_dir = PROJECTS_DIR / project
    subprocess.run([
        "tmux", "new-session", "-d", "-s", session,
        "-c", str(project_dir), CLAUDE_LAUNCH_CMD,
    ])
    time.sleep(2)  # let Claude Code boot before anything is typed into it


def send_prompt(project):
    session = f"{TMUX_SESSION_PREFIX}{project}"
    subprocess.run(["tmux", "send-keys", "-t", session, SCAN_PROMPT, "Enter"])


def hibernate(project):
    session = f"{TMUX_SESSION_PREFIX}{project}"
    subprocess.run(["tmux", "kill-session", "-t", session], capture_output=True)


def main_loop():
    idx = 0
    while True:
        pool = load_selected()

        if not pool:
            write_state(active_project=None, phase="idle", pool=[])
            time.sleep(IDLE_POOL_SLEEP)
            continue

        idx %= len(pool)
        project = pool[idx]

        pending = pending_count(project)

        if pending > 0:
            if not tmux_alive(project):
                write_state(active_project=project, phase="waking", pending=pending, pool=pool)
                spawn_session(project)
            write_state(active_project=project, phase="processing", pending=pending, pool=pool)
            send_prompt(project)
            time.sleep(POLL_WHILE_PROCESSING)
            continue  # stay on this project, check again next loop

        # Nothing pending right now.
        if tmux_alive(project):
            # It had been working — give it one grace period before giving up.
            write_state(active_project=project, phase="waiting", pending=0, pool=pool)
            time.sleep(EMPTY_GRACE_SECONDS)
            if pending_count(project) == 0:
                write_state(active_project=project, phase="hibernating", pending=0, pool=pool)
                hibernate(project)
            idx = (idx + 1) % len(pool)
        else:
            # Already quiet, nothing to wake for — just move on.
            write_state(active_project=project, phase="hibernating", pending=0, pool=pool)
            idx = (idx + 1) % len(pool)
            time.sleep(BETWEEN_PROJECT_PAUSE)


if __name__ == "__main__":
    main_loop()
