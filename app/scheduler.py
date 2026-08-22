#!/usr/bin/env python3
"""
Claude Code round-robin scheduler.

Runs continuously, independent of the dashboard web app. Cycles through
whichever projects are currently selected (state/selected_projects.json,
written by the dashboard) and, for each:

  1. Check its _Requests/ folder for READY items (cheap -- just a
     directory listing + first-line reads, no Claude session needed for
     this part). See common.py / _Instructions/Requests.md for exactly
     what counts as "ready".
  2. If there are pending items: make sure that project's tmux/Claude
     Code session is running (start it if not), send it a prompt to
     process the requests, then loop back and check again shortly after.
  3. If empty: wait EMPTY_GRACE_SECONDS and check once more.
  4. If still empty on that second check: hibernate the session (kill
     the tmux session to free RAM) and move to the next selected
     project.
  5. If nothing was ever running for this project, just move on straight
     away -- no point spawning Claude just to confirm there's nothing to
     do.

Writes its current state to state/scheduler_state.json so the dashboard
can display it, and appends transition events to state/activity_log.jsonl
so the dashboard can show a status log.

Run:
  python3 scheduler.py
(intended to run as a systemd service -- see ../systemd/bdrgui-scheduler.service)
"""

import json
import subprocess
import time
from datetime import datetime, timezone

import common

EMPTY_GRACE_SECONDS = 30       # wait this long after first empty scan before rechecking
POLL_WHILE_PROCESSING = 5      # how long to wait between rechecks while there's work
IDLE_POOL_SLEEP = 5            # how long to sleep if no projects are selected at all
BETWEEN_PROJECT_PAUSE = 2      # brief pause when moving on from an already-quiet project

SCAN_PROMPT = "Check the requests folder for new or updated files and process them now."


def write_state(active_project, phase, pending=None, pool=None):
    common.SCHEDULER_STATE_FILE.write_text(
        json.dumps({
            "active_project": active_project,
            "phase": phase,
            "pending": pending,
            "rotation_pool": pool if pool is not None else common.load_selected(),
            "last_update": datetime.now(timezone.utc).isoformat(),
        }, indent=2)
    )


def tmux_alive(project):
    session = f"{common.TMUX_SESSION_PREFIX}{project}"
    try:
        return subprocess.run(["tmux", "has-session", "-t", session], capture_output=True).returncode == 0
    except FileNotFoundError:
        return False


def spawn_session(project):
    session = f"{common.TMUX_SESSION_PREFIX}{project}"
    project_dir = common.PROJECTS_DIR / project
    subprocess.run([
        "tmux", "new-session", "-d", "-s", session,
        "-c", str(project_dir), common.CLAUDE_LAUNCH_CMD,
    ])
    time.sleep(2)  # let Claude Code boot before anything is typed into it


def send_prompt(project):
    session = f"{common.TMUX_SESSION_PREFIX}{project}"
    subprocess.run(["tmux", "send-keys", "-t", session, SCAN_PROMPT, "Enter"])


def hibernate(project):
    session = f"{common.TMUX_SESSION_PREFIX}{project}"
    subprocess.run(["tmux", "kill-session", "-t", session], capture_output=True)


def main_loop():
    idx = 0
    last_seen_pending = {}  # project -> last pending count we logged, for edge-triggered logging

    while True:
        pool = common.load_selected()

        if not pool:
            write_state(active_project=None, phase="idle", pool=[])
            time.sleep(IDLE_POOL_SLEEP)
            continue

        idx %= len(pool)
        project = pool[idx]

        pending = common.pending_count(project)
        if pending != last_seen_pending.get(project):
            if pending > 0:
                common.log_event(project, "requests_ready", {"pending": pending})
            last_seen_pending[project] = pending

        if pending > 0:
            if not tmux_alive(project):
                write_state(active_project=project, phase="waking", pending=pending, pool=pool)
                common.log_event(project, "session_waking", {"pending": pending})
                spawn_session(project)
            write_state(active_project=project, phase="processing", pending=pending, pool=pool)
            send_prompt(project)
            time.sleep(POLL_WHILE_PROCESSING)
            continue  # stay on this project, check again next loop

        # Nothing pending right now.
        if tmux_alive(project):
            # It had been working -- give it one grace period before giving up.
            write_state(active_project=project, phase="waiting", pending=0, pool=pool)
            time.sleep(EMPTY_GRACE_SECONDS)
            if common.pending_count(project) == 0:
                write_state(active_project=project, phase="hibernating", pending=0, pool=pool)
                common.log_event(project, "session_hibernated")
                hibernate(project)
                last_seen_pending[project] = 0
            idx = (idx + 1) % len(pool)
        else:
            # Already quiet, nothing to wake for -- just move on.
            write_state(active_project=project, phase="hibernating", pending=0, pool=pool)
            idx = (idx + 1) % len(pool)
            time.sleep(BETWEEN_PROJECT_PAUSE)


if __name__ == "__main__":
    main_loop()
