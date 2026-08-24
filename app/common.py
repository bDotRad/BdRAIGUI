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
SCHEDULER_START_FILE = STATE_DIR / "scheduler_start.json"
THEME_FILE = STATE_DIR / "theme.json"
ACTIVITY_LOG_MAX_LINES = 500

# Colour palette the admin tab can edit -- CSS custom properties on :root,
# keyed by the same name used in index.html's stylesheet (without the
# leading "--"). DEFAULT_THEME doubles as both the fallback values and the
# allow-list of which variables are editable at all.
DEFAULT_THEME = {
    "bg": "#0f1115",
    "card": "#171a21",
    "card-border": "#262b35",
    "text": "#e7e9ee",
    "text-dim": "#8b90a0",
    "accent": "#4f8cff",
    "title-color": "#e7e9ee",
}

REQUESTS_SUBDIR = "_Requests"
SHELVED_SUBDIR = "_Shelved"
STATUS_SUBDIR = ".claude-status"
STATUS_FILENAME = "status.json"
SQL_OUTPUT_CANDIDATES = ("sql_output.txt", "sql_output.sql")
ARCHIVE_SUBDIR_CANDIDATES = ("_Archive", "_Archived")
TEXT_FILE_SUFFIXES = {".md", ".txt", ".sql", ".py", ".json", ".html", ".yml", ".yaml", ".sh", ".service"}
IMAGE_FILE_SUFFIXES = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".svg"}
AGENT_FILES_SUBDIR = Path(".claude") / "agents"
DESCRIPTION_FILENAMES = ("Description.md", "description.md")

TMUX_SESSION_PREFIX = "proj-"
CLAUDE_LAUNCH_CMD = os.environ.get("CLAUDE_LAUNCH_CMD") or shutil.which("claude") or "claude"

# A permanent, always-on Claude Code session the scheduler keeps alive
# separately from the project rotation -- runs from PROJECTS_DIR itself
# (not any single project's directory), for checking whether other
# projects' sessions are stuck and running general cross-project commands.
# Reuses the same tmux-session/console-popup machinery as a real project
# (tmux_alive/tmux_capture/tmux_send, api_console/api_console/send) by
# treating this name as a pseudo-project everywhere except list_projects().
INDEPENDENT_SESSION = "_IndependentClaude"


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


_HEX_COLOR_RE = re.compile(r"^#[0-9a-fA-F]{6}$")


def load_theme():
    """Current colour palette, defaults filled in for anything unset/invalid."""
    theme = dict(DEFAULT_THEME)
    if THEME_FILE.exists():
        try:
            saved = json.loads(THEME_FILE.read_text())
        except (json.JSONDecodeError, OSError):
            saved = {}
        for key, value in saved.items():
            if key in DEFAULT_THEME and isinstance(value, str) and _HEX_COLOR_RE.match(value):
                theme[key] = value
    return theme


def save_theme(overrides):
    """Persist a full palette, validating against the DEFAULT_THEME allow-list.
    Unknown keys are dropped; invalid hex values are rejected outright."""
    theme = {}
    for key in DEFAULT_THEME:
        value = overrides.get(key, DEFAULT_THEME[key])
        if not isinstance(value, str) or not _HEX_COLOR_RE.match(value):
            raise ValueError(f"invalid colour for {key!r}: {value!r}")
        theme[key] = value
    THEME_FILE.write_text(json.dumps(theme))
    return theme


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


_MARKERS = ("READY", "NOT READY", "WAITING RESPONSE")

# Reserved names that read as reference material, not requests, even though
# they don't start with the '_'/'.'/'x'/'X' ignore-prefixes -- e.g. a
# project's own copy of the request-intake convention doc, dropped directly
# in _Requests/ as README.md rather than under _Archive/. See the incident
# this guards against in _Requests/_Archive/ (BdRBirdDetector/_Requests/
# README.md got its first line clobbered by "Mark Ready" before this existed).
_RESERVED_REQUEST_NAMES = {"readme", "readme.md", "readme.txt"}


def _is_request_entry(name):
    """Whether an item name directly under _Requests/ should be treated as
    a request at all (vs. skipped as archive/meta/ignored/reference)."""
    if name.startswith(("_", ".", "x", "X")):
        return False
    if name.lower() in _RESERVED_REQUEST_NAMES:
        return False
    return True


def _request_marker(item):
    """Raw marker line for one _Requests/ entry (file or folder), defaulting
    to "NOT READY" for anything without a clear marker."""
    if item.is_file():
        if item.suffix.lower() != ".md":
            return "NOT READY"
        first = _first_line(item)
        return first if first in _MARKERS else "NOT READY"

    if item.is_dir():
        md_files = sorted(p for p in item.iterdir() if p.is_file() and p.suffix.lower() == ".md")
        for md in md_files:
            first = _first_line(md)
            if first in _MARKERS:
                return first
        return "NOT READY"

    return "NOT READY"


def _is_ready(item):
    """READY/NOT READY state for one _Requests/ entry (file or folder)."""
    return _request_marker(item) == "READY"


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
        if not _is_request_entry(name):
            continue
        total += 1
        if _is_ready(item):
            ready += 1
    return ready, total


def pending_count(project):
    ready, _total = scan_requests(project)
    return ready


# ---- Archived requests (browse-only) ------------------------------------------

def find_archive_dir(project):
    req_dir = PROJECTS_DIR / project / REQUESTS_SUBDIR
    for name in ARCHIVE_SUBDIR_CANDIDATES:
        candidate = req_dir / name
        if candidate.is_dir():
            return candidate
    return None


def list_archive(project, subpath=""):
    """List one level of a project's archive folder, newest-first.

    `subpath` (relative to the archive dir) lets the UI expand into a
    folder entry (e.g. `rf Logo Sq/`). The archiver prepends `YYMMDD_HHMM_`
    to names, so a reverse name sort is also a reverse-chronological sort;
    older pre-convention entries without the date prefix just sort in
    among themselves.
    """
    archive_dir = find_archive_dir(project)
    if archive_dir is None:
        return None
    target = (archive_dir / subpath).resolve() if subpath else archive_dir
    try:
        target.relative_to(archive_dir.resolve())
    except ValueError:
        return None
    if not target.is_dir():
        return None

    entries = []
    for item in target.iterdir():
        entries.append({
            "name": item.name,
            "is_dir": item.is_dir(),
            "mtime_relative": file_mtime_relative(item),
        })
    entries.sort(key=lambda e: e["name"].lower(), reverse=True)
    return entries


def resolve_archive_file(project, rel_path):
    """Validated absolute Path to a file inside a project's archive folder,
    or None if it's missing or would escape the archive dir."""
    archive_dir = find_archive_dir(project)
    if archive_dir is None:
        return None
    archive_dir = archive_dir.resolve()
    target = (archive_dir / rel_path).resolve()
    try:
        target.relative_to(archive_dir)
    except ValueError:
        return None
    if not target.is_file():
        return None
    return target


def read_archive_file(project, rel_path):
    """Read a text file inside a project's archive folder, path-checked.
    Images report back as `image: True` (no inline content -- fetched
    separately via the raw-bytes route) rather than as opaque binary."""
    target = resolve_archive_file(project, rel_path)
    if target is None:
        return None
    suffix = target.suffix.lower()
    if suffix in IMAGE_FILE_SUFFIXES:
        return {"text": False, "image": True, "content": None}
    if suffix not in TEXT_FILE_SUFFIXES:
        return {"text": False, "image": False, "content": None}
    try:
        return {"text": True, "image": False, "content": target.read_text(errors="replace")}
    except OSError:
        return None


# ---- Project description / Claude agent files (browse-only) -------------------

def find_description_file(project):
    proj_dir = PROJECTS_DIR / project
    for name in DESCRIPTION_FILENAMES:
        candidate = proj_dir / name
        if candidate.is_file():
            return candidate
    return None


def list_agent_files(project):
    """CLAUDE.md at project root, plus any .md files under .claude/agents/."""
    proj_dir = PROJECTS_DIR / project
    files = []

    claude_md = proj_dir / "CLAUDE.md"
    if claude_md.is_file():
        files.append(claude_md)

    agents_dir = proj_dir / AGENT_FILES_SUBDIR
    if agents_dir.is_dir():
        files.extend(sorted(agents_dir.rglob("*.md")))

    return files


def read_project_file(project, rel_path):
    """Read a text file inside a project dir, restricted to the description
    file or one of list_agent_files() -- not an arbitrary path."""
    proj_dir = PROJECTS_DIR / project
    allowed = {find_description_file(project)} | set(list_agent_files(project))
    allowed.discard(None)
    allowed_rel = {str(p.relative_to(proj_dir)) for p in allowed}
    if rel_path not in allowed_rel:
        return None
    target = proj_dir / rel_path
    try:
        return target.read_text(errors="replace")
    except OSError:
        return None


def write_description_file(project, content):
    """Overwrite (or create) a project's Description.md. Only ever touches
    the description file -- never CLAUDE.md or .claude/agents/ files, which
    stay browse-only from the dashboard."""
    proj_dir = PROJECTS_DIR / project
    target = find_description_file(project) or (proj_dir / DESCRIPTION_FILENAMES[0])
    try:
        target.write_text(content)
    except OSError:
        return False
    return True


# ---- Request creation (web UI "drop a request" form) --------------------------

_TITLE_ILLEGAL_RE = re.compile(r'[\\/:*?"<>|]')
_TITLE_WHITESPACE_RE = re.compile(r"\s+")


def sanitize_title(title):
    """Clean up a user-typed title for use in a filename: strip characters
    illegal on common filesystems and collapse whitespace. Spaces and case
    are otherwise preserved so the title stays human-readable on disk."""
    title = _TITLE_ILLEGAL_RE.sub("", title)
    title = _TITLE_WHITESPACE_RE.sub(" ", title).strip()
    return title or "Untitled"


def request_title(stem):
    """Recover a human title from a _Requests/ item's name.

    Convention: request filenames are 'r' + Title (e.g. `rLogo resize.md`
    has title "Logo resize", `rf Logo Sq/` has title "f Logo Sq"). Strips a
    single leading 'r'/'R'; falls back to the raw name if that would leave
    nothing (e.g. a bare `r.md`), or if the name doesn't start with 'r' at
    all (old numbered requests, or anything dropped in directly under a
    different naming scheme).
    """
    if stem[:1] in ("r", "R") and len(stem) > 1:
        return stem[1:].strip()
    return stem


def _unique_request_name(req_dir, base):
    """`base` (no extension) with a numeric suffix appended if needed to
    avoid colliding with an existing rTitle.md file or rTitle/ folder."""
    candidate = base
    n = 2
    while (req_dir / f"{candidate}.md").exists() or (req_dir / candidate).exists():
        candidate = f"{base} {n}"
        n += 1
    return candidate


def create_request_file(project, title, content, ready):
    """Write _Requests/r<Title>.md for `project`. Returns the created Path."""
    req_dir = PROJECTS_DIR / project / REQUESTS_SUBDIR
    req_dir.mkdir(parents=True, exist_ok=True)
    base = f"r{sanitize_title(title)}"
    name = _unique_request_name(req_dir, base)
    path = req_dir / f"{name}.md"
    marker = "READY" if ready else "NOT READY"
    path.write_text(f"{marker}\n\n{content}\n")
    return path


def create_request_folder(project, title, content, ready, attachments):
    """Make _Requests/r<Title>/ with request.md + attachment files. Returns the folder Path."""
    req_dir = PROJECTS_DIR / project / REQUESTS_SUBDIR
    req_dir.mkdir(parents=True, exist_ok=True)
    base = f"r{sanitize_title(title)}"
    name = _unique_request_name(req_dir, base)
    folder = req_dir / name
    folder.mkdir()
    marker = "READY" if ready else "NOT READY"
    (folder / "request.md").write_text(f"{marker}\n\n{content}\n")
    for f in attachments:
        fname = os.path.basename(f.filename or "")
        if not fname:
            continue
        f.save(folder / fname)
    return folder


_REQUEST_STATUS_SORT = {"Waiting Response": 0, "Processing": 1, "Ready": 2, "Not Ready": 3}
QUESTION_EXCERPT_LENGTH = 280


def _question_excerpt(target):
    """Body text of a request's .md file (marker line + blank line stripped),
    truncated for display. Used to surface *what* a Waiting Response item is
    actually blocked on, without opening the file."""
    if target is None:
        return None
    try:
        text = target.read_text(errors="replace")
    except OSError:
        return None
    body = text.split("\n", 1)[1].strip() if "\n" in text else ""
    if not body:
        return None
    if len(body) > QUESTION_EXCERPT_LENGTH:
        body = body[:QUESTION_EXCERPT_LENGTH].rstrip() + "…"
    return body


def list_requests(project, active_processing=False):
    """List a project's outstanding _Requests/ items with title + display status.

    Mirrors scan_requests()'s filtering (skips _/./x/X-prefixed entries).
    `active_processing` should be True when this project is the scheduler's
    active project and mid-pass (phase == "processing") -- while that's
    true, READY items show as "Processing" rather than "Ready", since
    they're what's actively being worked through right now.

    Sorted with Waiting Response items first (they need a human to look at
    them; everything else the scheduler already has in hand), then
    Processing, Ready, Not Ready -- alphabetically by title within each.
    """
    req_dir = PROJECTS_DIR / project / REQUESTS_SUBDIR
    if not req_dir.exists():
        return []

    items = []
    for item in req_dir.iterdir():
        name = item.name
        if not _is_request_entry(name):
            continue
        marker = _request_marker(item)
        if marker == "WAITING RESPONSE":
            status = "Waiting Response"
        elif marker == "READY":
            status = "Processing" if active_processing else "Ready"
        else:
            status = "Not Ready"
        stem = item.stem if item.is_file() else item.name
        title = request_title(stem)
        entry = {
            "name": name,
            "title": title,
            "status": status,
            "is_folder": item.is_dir(),
        }
        if status == "Waiting Response":
            entry["question"] = _question_excerpt(_resolve_request_target(project, name))
        items.append(entry)

    items.sort(key=lambda e: (_REQUEST_STATUS_SORT.get(e["status"], 9), e["title"].lower()))
    return items


def _resolve_request_target(project, name):
    """Path to the .md file that list_requests()/_request_marker() read the
    status from for one _Requests/ item, or None if `name` doesn't resolve
    to a real item (or would escape _Requests/).

    `name` is the file/folder name as returned by list_requests() (not a
    full path) -- rejected outright if it isn't a plain basename. For a
    folder item, picks whichever .md file carries a marker (falling back to
    request.md, then the first .md alphabetically), same rule
    _request_marker() uses.
    """
    if not name or os.path.basename(name) != name or not _is_request_entry(name):
        return None
    req_dir = PROJECTS_DIR / project / REQUESTS_SUBDIR
    item = req_dir / name
    if not item.exists():
        return None

    if item.is_file():
        return item
    if item.is_dir():
        md_files = sorted(p for p in item.iterdir() if p.is_file() and p.suffix.lower() == ".md")
        target = next((md for md in md_files if _first_line(md) in _MARKERS), None)
        if target is None:
            request_md = item / "request.md"
            target = request_md if request_md in md_files else (md_files[0] if md_files else None)
        return target
    return None


def set_request_ready(project, name):
    """Flip one _Requests/ item's marker line to READY, in place.
    Returns True if a marker was flipped.
    """
    target = _resolve_request_target(project, name)
    if target is None:
        return False
    try:
        text = target.read_text(errors="replace")
    except OSError:
        return False
    _, _, rest = text.partition("\n")
    try:
        target.write_text("READY\n" + rest)
    except OSError:
        return False
    return True


def set_request_not_ready(project, name, console_snapshot=None):
    """Flip one _Requests/ item's marker line to NOT READY, in place.

    A request usually gets pulled back to NOT READY while its session is
    still live and mid-thought -- pass that session's current console
    content as `console_snapshot` (see tmux_capture()) and it's appended to
    the request body under a dated header before the flip, instead of being
    lost the moment the tmux pane moves on. Whatever's in there next time
    the request is reopened is then still around to read.
    Returns True if a marker was flipped.
    """
    target = _resolve_request_target(project, name)
    if target is None:
        return False
    try:
        text = target.read_text(errors="replace")
    except OSError:
        return False
    _, _, rest = text.partition("\n")
    if console_snapshot and console_snapshot.strip():
        stamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        rest = (
            rest.rstrip("\n")
            + f"\n\n---\n\nConsole snapshot when marked Not Ready ({stamp}):\n\n"
            + f"```\n{console_snapshot.rstrip()}\n```\n"
        )
    try:
        target.write_text("NOT READY\n" + rest)
    except OSError:
        return False
    return True


def read_request_body(project, name):
    """Body text of one _Requests/ item (everything after the marker line),
    for editing in the UI. Returns None if `name` doesn't resolve to a
    real item."""
    target = _resolve_request_target(project, name)
    if target is None:
        return None
    try:
        text = target.read_text(errors="replace")
    except OSError:
        return None
    _, _, rest = text.partition("\n")
    return rest.lstrip("\n")


def write_request_body(project, name, body):
    """Overwrite one _Requests/ item's body, keeping its existing marker
    line untouched. Returns True if the write happened."""
    target = _resolve_request_target(project, name)
    if target is None:
        return False
    try:
        text = target.read_text(errors="replace")
    except OSError:
        return False
    marker, _, _ = text.partition("\n")
    if marker not in _MARKERS:
        marker = "NOT READY"
    try:
        target.write_text(f"{marker}\n\n{body.strip()}\n")
    except OSError:
        return False
    return True


# ---- Shelving (park a request aside without deleting or archiving it) --------

def _request_item_path(project, name):
    """Path to the top-level _Requests/ entry named `name` (the whole file
    or whole folder, not its marker file) -- for operations that move or
    remove the item itself. None if `name` doesn't resolve to a real item."""
    if not name or os.path.basename(name) != name or not _is_request_entry(name):
        return None
    item = PROJECTS_DIR / project / REQUESTS_SUBDIR / name
    return item if item.exists() else None


def _shelved_item_path(project, name):
    """Path to the entry named `name` directly under _Requests/_Shelved/,
    or None if it doesn't exist."""
    if not name or os.path.basename(name) != name:
        return None
    item = PROJECTS_DIR / project / REQUESTS_SUBDIR / SHELVED_SUBDIR / name
    return item if item.exists() else None


def _move_unique(src, dest_dir):
    """Move `src` (file or folder) into `dest_dir`, appending a numeric
    suffix to the name if something's already there under that name."""
    dest_dir.mkdir(parents=True, exist_ok=True)
    stem = src.stem if src.is_file() else src.name
    suffix = src.suffix if src.is_file() else ""
    candidate = src.name
    n = 2
    while (dest_dir / candidate).exists():
        candidate = f"{stem} {n}{suffix}"
        n += 1
    dest = dest_dir / candidate
    shutil.move(str(src), str(dest))
    return dest


def shelve_request(project, name):
    """Move one _Requests/ item into _Requests/_Shelved/, out of the
    scheduler's way without deleting or archiving it. Returns True on
    success."""
    item = _request_item_path(project, name)
    if item is None:
        return False
    shelved_dir = PROJECTS_DIR / project / REQUESTS_SUBDIR / SHELVED_SUBDIR
    try:
        _move_unique(item, shelved_dir)
    except OSError:
        return False
    return True


def list_shelved(project):
    """List items sitting in a project's _Requests/_Shelved/ folder."""
    shelved_dir = PROJECTS_DIR / project / REQUESTS_SUBDIR / SHELVED_SUBDIR
    if not shelved_dir.exists():
        return []
    items = []
    for item in sorted(shelved_dir.iterdir(), key=lambda p: p.name.lower()):
        if item.name.startswith("."):
            continue
        stem = item.stem if item.is_file() else item.name
        items.append({
            "name": item.name,
            "title": request_title(stem),
            "is_folder": item.is_dir(),
        })
    return items


def unshelve_request(project, name):
    """Move one _Requests/_Shelved/ item back into _Requests/, marker
    untouched. Returns True on success."""
    item = _shelved_item_path(project, name)
    if item is None:
        return False
    req_dir = PROJECTS_DIR / project / REQUESTS_SUBDIR
    try:
        _move_unique(item, req_dir)
    except OSError:
        return False
    return True


def delete_shelved_request(project, name):
    """Permanently delete one _Requests/_Shelved/ item. Returns True on
    success."""
    item = _shelved_item_path(project, name)
    if item is None:
        return False
    try:
        if item.is_dir():
            shutil.rmtree(item)
        else:
            item.unlink()
    except OSError:
        return False
    return True


# ---- Live console (peek at / reply to a project's tmux session) --------------

# ---- Dashboard self-admin (restart status) -----------------------------------

DASHBOARD_WATCH_FILES = (APP_DIR / "dashboard.py", APP_DIR / "common.py")
DASHBOARD_WATCH_DIRS = (APP_DIR / "templates", APP_DIR / "static")

# A Claude session editing these files (its own dashboard/scheduler code)
# typically touches several of them in a row over a few seconds. Requiring
# the newest watched mtime to be at least this old before flagging a
# restart means the flag settles once after a whole edit batch, instead of
# flapping true/false/true as each individual file save lands -- which
# otherwise reads as "restart, running, needs another restart" to Brad
# even though nothing's actually finished changing yet.
RESTART_DEBOUNCE_SECONDS = 5


def dashboard_needs_restart(start_time):
    """True if a dashboard source file (app/*.py, templates/, static/) was
    modified after this process started, and that edit has been sitting
    for a bit (see RESTART_DEBOUNCE_SECONDS). Flask runs with debug=False
    and no autoreload, so such changes need a process restart to take
    effect."""
    newest = None
    for f in DASHBOARD_WATCH_FILES:
        try:
            mtime = f.stat().st_mtime
        except OSError:
            continue
        if newest is None or mtime > newest:
            newest = mtime
    for d in DASHBOARD_WATCH_DIRS:
        if not d.is_dir():
            continue
        for f in d.rglob("*"):
            if not f.is_file():
                continue
            try:
                mtime = f.stat().st_mtime
            except OSError:
                continue
            if newest is None or mtime > newest:
                newest = mtime
    if newest is None or newest <= start_time:
        return False
    return (time.time() - newest) >= RESTART_DEBOUNCE_SECONDS


SCHEDULER_WATCH_FILES = (APP_DIR / "scheduler.py", APP_DIR / "common.py")


def record_scheduler_start():
    """Called once by scheduler.py at startup so the dashboard (a separate
    process) can later tell whether scheduler.py/common.py have changed
    since this run began."""
    SCHEDULER_START_FILE.write_text(json.dumps({"start_time": time.time()}))


def scheduler_needs_restart():
    """True if a scheduler source file was modified after the running
    scheduler process started, and that edit has settled (see
    RESTART_DEBOUNCE_SECONDS). Mirrors dashboard_needs_restart, but reads
    the start time back from disk since the dashboard isn't the process
    that recorded it."""
    try:
        start_time = json.loads(SCHEDULER_START_FILE.read_text())["start_time"]
    except (OSError, ValueError, KeyError):
        return False
    newest = None
    for f in SCHEDULER_WATCH_FILES:
        try:
            mtime = f.stat().st_mtime
        except OSError:
            continue
        if newest is None or mtime > newest:
            newest = mtime
    if newest is None or newest <= start_time:
        return False
    return (time.time() - newest) >= RESTART_DEBOUNCE_SECONDS


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


_CLI_RULE_RE = re.compile(r"^\s*─{10,}\s*$")


def _strip_cli_chrome(content, tail_window=20):
    """Drop Claude Code's fixed bottom UI (input box, mode line, agent list).

    That chrome is redrawn in place every frame using a pair of Unicode
    box-drawing rules (─) around the input box, so its top rule is a
    reliable marker for "everything below here is static, not transcript".
    Only match within the last `tail_window` lines so a `---`-style rule
    that's part of real scrollback content isn't mistaken for it.
    """
    lines = content.splitlines()
    start = max(0, len(lines) - tail_window)
    for i in range(start, len(lines)):
        if _CLI_RULE_RE.match(lines[i]):
            return "\n".join(lines[:i]).rstrip("\n") + "\n"
    return content


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
        return _strip_cli_chrome(out.stdout)
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


# Keys the console UI is allowed to send raw (no text, no trailing Enter) --
# a small whitelist so /api/console/<project>/key can't become an arbitrary
# key-injection endpoint. C-o is Claude Code's own "expand" toggle for a
# collapsed background-agent status line.
ALLOWED_CONSOLE_KEYS = {"C-o"}


def tmux_send_key(project, key):
    """Send a single raw key (e.g. `C-o`) into the project's tmux session.

    Unlike tmux_send, this doesn't type text or submit with Enter -- it's for
    toggling Claude Code's own UI state (like expanding a collapsed
    background-agent line), not for sending a message into the session.
    """
    if key not in ALLOWED_CONSOLE_KEYS:
        return False
    if not tmux_alive(project):
        return False
    session = tmux_session_name(project)
    try:
        subprocess.run(["tmux", "send-keys", "-t", session, key], timeout=5)
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


_APP_VERSION_CACHE = None


def app_version():
    """Version string for this app's own running code: the current
    commit's date/time (yymmdd_hhmmss, local) plus its short hash. Since
    Flask runs with no autoreload, this is stable for the life of the
    process -- computed once and cached."""
    global _APP_VERSION_CACHE
    if _APP_VERSION_CACHE is not None:
        return _APP_VERSION_CACHE
    repo_dir = APP_DIR.parent
    try:
        out = subprocess.run(
            ["git", "log", "-1", "--format=%cd %h", "--date=format-local:%y%m%d_%H%M%S"],
            cwd=repo_dir, capture_output=True, text=True, timeout=3,
        )
        version = out.stdout.strip() if out.returncode == 0 else ""
    except (subprocess.TimeoutExpired, OSError):
        version = ""
    _APP_VERSION_CACHE = version or "unknown"
    return _APP_VERSION_CACHE


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
