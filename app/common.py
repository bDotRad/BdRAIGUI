"""
Shared helpers for dashboard.py and scheduler.py.

Both processes need to agree on exactly what counts as a "pending
request" for a project, so that scanning logic lives in one place. See
../_Instructions/Requests.md for the request-intake convention this
implements (READY/NOT READY marker, x-prefix to ignore, _-prefix for
archive/meta folders).
"""

import json
import os
import re
import shutil
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = APP_DIR.parent

PROJECTS_DIR = Path(os.environ.get("PROJECTS_DIR", Path.home() / "projects"))
STATE_DIR = Path(os.environ.get("STATE_DIR", PROJECT_ROOT / "state"))
STATE_DIR.mkdir(parents=True, exist_ok=True)

SELECTED_FILE = STATE_DIR / "selected_projects.json"
SCHEDULER_STATE_FILE = STATE_DIR / "scheduler_state.json"
ACTIVITY_LOG_FILE = STATE_DIR / "activity_log.jsonl"
ACTIVITY_LOG_MAX_LINES = 500

REQUESTS_SUBDIR = "_Requests"
STATUS_SUBDIR = ".claude-status"
STATUS_FILENAME = "status.json"
SQL_OUTPUT_CANDIDATES = ("sql_output.txt", "sql_output.sql")

TMUX_SESSION_PREFIX = "proj-"
CLAUDE_LAUNCH_CMD = os.environ.get("CLAUDE_LAUNCH_CMD") or shutil.which("claude") or "claude"


# ---- Project listing / rotation selection -----------------------------------

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


# ---- Request scanning (READY/NOT READY convention) ---------------------------

def _first_line(path):
    try:
        with path.open("r", errors="replace") as f:
            return f.readline().strip()
    except OSError:
        return ""


def _is_ready(item):
    """READY/NOT READY state for one _Requests/ entry (file or folder)."""
    if item.is_file():
        if item.suffix.lower() != ".md":
            return False
        return _first_line(item) == "READY"

    if item.is_dir():
        md_files = sorted(p for p in item.iterdir() if p.is_file() and p.suffix.lower() == ".md")
        for md in md_files:
            first = _first_line(md)
            if first in ("READY", "NOT READY"):
                return first == "READY"
        return False

    return False


def scan_requests(project):
    """Return (ready_count, total_count) for a project's _Requests/ folder.

    Ignores anything prefixed with '_' (archive/meta folders like
    _Archive, _Archived) or 'x'/'X' (explicitly-ignored items).
    """
    req_dir = PROJECTS_DIR / project / REQUESTS_SUBDIR
    if not req_dir.exists():
        return 0, 0

    ready = 0
    total = 0
    for item in req_dir.iterdir():
        name = item.name
        if name.startswith(("_", ".", "x", "X")):
            continue
        total += 1
        if _is_ready(item):
            ready += 1
    return ready, total


def pending_count(project):
    ready, _total = scan_requests(project)
    return ready


# ---- Request creation (web UI "drop a request" form) --------------------------

_REQUEST_NUM_RE = re.compile(r"^[rR](\d+)")


def _next_request_number(req_dir):
    """Smallest unused N across existing rN.md files / rN/ folders."""
    highest = 0
    if req_dir.exists():
        for item in req_dir.iterdir():
            m = _REQUEST_NUM_RE.match(item.stem if item.is_file() else item.name)
            if m:
                highest = max(highest, int(m.group(1)))
    return highest + 1


def create_request_file(project, content, ready):
    """Write _Requests/rN.md for `project`. Returns the created Path."""
    req_dir = PROJECTS_DIR / project / REQUESTS_SUBDIR
    req_dir.mkdir(parents=True, exist_ok=True)
    num = _next_request_number(req_dir)
    path = req_dir / f"r{num}.md"
    marker = "READY" if ready else "NOT READY"
    path.write_text(f"{marker}\n\n{content}\n")
    return path


def create_request_folder(project, content, ready, attachments):
    """Make _Requests/rN/ with request.md + attachment files. Returns the folder Path."""
    req_dir = PROJECTS_DIR / project / REQUESTS_SUBDIR
    req_dir.mkdir(parents=True, exist_ok=True)
    num = _next_request_number(req_dir)
    folder = req_dir / f"r{num}"
    folder.mkdir()
    marker = "READY" if ready else "NOT READY"
    (folder / "request.md").write_text(f"{marker}\n\n{content}\n")
    for f in attachments:
        name = os.path.basename(f.filename or "")
        if not name:
            continue
        f.save(folder / name)
    return folder


# ---- Live console (peek at / reply to a project's tmux session) --------------

def tmux_session_name(project):
    return f"{TMUX_SESSION_PREFIX}{project}"


def tmux_alive(project):
    try:
        return subprocess.run(
            ["tmux", "has-session", "-t", tmux_session_name(project)],
            capture_output=True, timeout=5,
        ).returncode == 0
    except (subprocess.TimeoutExpired, OSError):
        return False


def tmux_capture(project, lines=300):
    """Snapshot of the project's tmux pane, or None if no session is running."""
    if not tmux_alive(project):
        return None
    try:
        out = subprocess.run(
            ["tmux", "capture-pane", "-t", tmux_session_name(project), "-p", "-S", f"-{lines}"],
            capture_output=True, text=True, timeout=5,
        )
        if out.returncode != 0:
            return None
        return out.stdout
    except (subprocess.TimeoutExpired, OSError):
        return None


def tmux_send(project, text):
    """Type `text` into the project's tmux session and submit it.

    Text and Enter are sent as two separate tmux calls with a brief pause --
    sending them in one burst gets treated as a paste by Claude Code's input
    box, so the trailing Enter lands as a newline instead of submitting.
    """
    if not tmux_alive(project):
        return False
    session = tmux_session_name(project)
    try:
        subprocess.run(["tmux", "send-keys", "-t", session, text], timeout=5)
        time.sleep(0.4)
        subprocess.run(["tmux", "send-keys", "-t", session, "Enter"], timeout=5)
        return True
    except (subprocess.TimeoutExpired, OSError):
        return False


# ---- Status / commit / sql-output readback -----------------------------------

def read_status(project):
    status_path = PROJECTS_DIR / project / STATUS_SUBDIR / STATUS_FILENAME
    if not status_path.exists():
        return {}
    try:
        return json.loads(status_path.read_text())
    except (json.JSONDecodeError, OSError):
        return {}


def find_sql_output(project):
    """Path to a pending SQL-output file for this project, if any."""
    status_dir = PROJECTS_DIR / project / STATUS_SUBDIR
    for name in SQL_OUTPUT_CANDIDATES:
        candidate = status_dir / name
        if candidate.exists():
            return candidate
    return None


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


def file_mtime_relative(path):
    return relative_time(
        datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).isoformat()
    )


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


# ---- Activity log --------------------------------------------------------------

def log_event(project, event, detail=None):
    """Append one event to the shared activity log (newest last on disk)."""
    entry = {
        "time": datetime.now(timezone.utc).isoformat(),
        "project": project,
        "event": event,
    }
    if detail is not None:
        entry["detail"] = detail

    with ACTIVITY_LOG_FILE.open("a") as f:
        f.write(json.dumps(entry) + "\n")

    _trim_log_if_needed()


def _trim_log_if_needed():
    if not ACTIVITY_LOG_FILE.exists():
        return
    try:
        lines = ACTIVITY_LOG_FILE.read_text().splitlines()
    except OSError:
        return
    if len(lines) > ACTIVITY_LOG_MAX_LINES * 2:
        keep = lines[-ACTIVITY_LOG_MAX_LINES:]
        ACTIVITY_LOG_FILE.write_text("\n".join(keep) + "\n")


def read_log(limit=50, project=None):
    if not ACTIVITY_LOG_FILE.exists():
        return []
    try:
        lines = ACTIVITY_LOG_FILE.read_text().splitlines()
    except OSError:
        return []

    entries = []
    for line in reversed(lines):
        if not line.strip():
            continue
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue
        if project and entry.get("project") != project:
            continue
        entries.append(entry)
        if len(entries) >= limit:
            break
    return entries
