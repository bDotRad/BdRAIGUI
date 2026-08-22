#!/usr/bin/env python3
"""
Claude Code project dashboard — display + rotation selection only.

All the round-robin scanning/switching logic lives in scheduler.py, a
separate always-on process. This app just:
  - shows each project's status (git, pending request count)
  - shows which project the scheduler currently has active, and its phase
    (processing / waiting / hibernating)
  - lets you tick which projects are in the scheduler's rotation pool

Run:
  python3 dashboard.py
Then open http://<pi-ip>:8420
"""

import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from flask import Flask, jsonify, render_template, request

app = Flask(__name__)

PROJECTS_DIR = Path(os.environ.get("PROJECTS_DIR", Path.home() / "projects"))
STATE_DIR = Path(os.environ.get("STATE_DIR", Path.home() / "claude-dashboard" / "state"))
STATE_DIR.mkdir(parents=True, exist_ok=True)

SELECTED_FILE = STATE_DIR / "selected_projects.json"
SCHEDULER_STATE_FILE = STATE_DIR / "scheduler_state.json"

STATUS_SUBDIR = ".claude-status"
STATUS_FILENAME = "status.json"


# ---- Helpers ----------------------------------------------------------------

def list_projects():
    if not PROJECTS_DIR.exists():
        return []
    return sorted(
        p.name for p in PROJECTS_DIR.iterdir()
        if p.is_dir() and not p.name.startswith(".")
    )


def load_selected():
    if not SELECTED_FILE.exists():
        return []
    try:
        return json.loads(SELECTED_FILE.read_text())
    except (json.JSONDecodeError, OSError):
        return []


def save_selected(selected):
    SELECTED_FILE.write_text(json.dumps(selected))


def load_scheduler_state():
    if not SCHEDULER_STATE_FILE.exists():
        return {"active_project": None, "phase": "idle"}
    try:
        return json.loads(SCHEDULER_STATE_FILE.read_text())
    except (json.JSONDecodeError, OSError):
        return {"active_project": None, "phase": "idle"}


def read_status(project):
    status_path = PROJECTS_DIR / project / STATUS_SUBDIR / STATUS_FILENAME
    if not status_path.exists():
        return {}
    try:
        return json.loads(status_path.read_text())
    except (json.JSONDecodeError, OSError):
        return {}


def count_pending_requests(project):
    req_dir = PROJECTS_DIR / project / "requests"
    if not req_dir.exists():
        return 0
    return sum(1 for f in req_dir.iterdir() if f.is_file())


def last_commit(project):
    repo_dir = PROJECTS_DIR / project
    if not (repo_dir / ".git").exists():
        return None
    try:
        out = subprocess.run(
            ["git", "log", "-1", "--format=%h|%s|%cI"],
            cwd=repo_dir, capture_output=True, text=True, timeout=3,
        )
        if out.returncode != 0 or not out.stdout.strip():
            return None
        hash_, msg, iso_time = out.stdout.strip().split("|", 2)
        return {"hash": hash_, "message": msg, "time": iso_time}
    except (subprocess.TimeoutExpired, OSError, ValueError):
        return None


def relative_time(iso_str):
    if not iso_str:
        return None
    try:
        then = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
    except ValueError:
        return iso_str
    seconds = (datetime.now(timezone.utc) - then).total_seconds()
    if seconds < 60:
        return "just now"
    if seconds < 3600:
        return f"{int(seconds // 60)}m ago"
    if seconds < 86400:
        return f"{int(seconds // 3600)}h ago"
    return f"{int(seconds // 86400)}d ago"


# ---- Routes -------------------------------------------------------------------

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/status")
def api_status():
    scheduler = load_scheduler_state()
    selected = set(load_selected())
    active_project = scheduler.get("active_project")

    projects = []
    for name in list_projects():
        status = read_status(name)
        projects.append({
            "name": name,
            "in_rotation": name in selected,
            "is_active": active_project == name,
            "phase": scheduler.get("phase") if active_project == name else None,
            "current_task": status.get("current_task"),
            "last_active_relative": relative_time(status.get("last_active")),
            "pending_requests": count_pending_requests(name),
            "last_commit": last_commit(name),
        })

    return jsonify({
        "active_project": active_project,
        "phase": scheduler.get("phase"),
        "scheduler_last_update": scheduler.get("last_update"),
        "projects": projects,
    })


@app.route("/api/selected", methods=["POST"])
def api_select():
    data = request.get_json(force=True)
    project = data.get("project")
    want_selected = bool(data.get("selected"))

    if project not in list_projects():
        return jsonify({"ok": False, "error": "unknown project"}), 404

    selected = load_selected()
    if want_selected and project not in selected:
        selected.append(project)
    elif not want_selected and project in selected:
        selected.remove(project)
    save_selected(selected)
    return jsonify({"ok": True, "selected": selected})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8420, debug=False)
