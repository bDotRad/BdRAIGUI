## What was done

Two requests processed together (both READY):

### 1. Click a request's name to edit it

Previously, on the main dashboard's project cards, editing a request required
clicking a separate "Edit" button that only appeared for `Not Ready` items.
On the project detail page (`/project/<name>`), the requests table wasn't
clickable at all — no way to view/edit a request's body from there.

Changes:
- `app/templates/index.html`: the request title itself in each project
  card's mini request list is now clickable (`.req-mini-name`) and opens the
  existing edit-request modal, for any status (not just `Not Ready`). The
  separate "Edit" button was removed since the title now does that job;
  "Mark Ready" stays as its own button for `Not Ready` items.
- `app/templates/project.html`: the requests table had no editor at all.
  Added a simple inline editor — clicking a request's title loads its body
  into the existing file-view textarea (now made editable for this case),
  with Save/Cancel buttons that appear underneath. Uses the existing
  `/api/requests/<project>/content` GET/POST endpoints (already built for
  the dashboard's modal editor, just not wired up here yet).

No backend changes needed — `common.read_request_body`/`write_request_body`
already existed and don't care about a request's status.

### 2. Admin tab: service status + restart button

Added a new "Admin" tab (alongside Projects / Activity Log) on the main
dashboard:
- Shows a status badge: **Running** / **Requires Restart** / **Restarting…**
- "Restart service" button underneath, with a confirm prompt (brief outage).
- The tab label itself turns bright red-orange when a restart is required,
  visible from any tab (as asked).

**One deliberate deviation from the literal request:** the request said the
restart button should run `sudo systemctl restart bdraigui-dashboard`. Per
this project's own CLAUDE.md ("No sudo here... needs Brad to run it by
hand"), confirmed live with `sudo -n -l` → `sudo: interactive authentication
is required`. A button that shelled out to that command would just hang/fail
on every click. Used the mechanism CLAUDE.md documents instead: the process
sends itself `SIGKILL` (`os.kill(os.getpid(), signal.SIGKILL)`), which
systemd's `Restart=on-failure` treats as a crash and relaunches within
`RestartSec=3` — no sudo needed, since a process can always signal itself.
Functionally this gives Brad exactly what he asked for (a working one-click
restart from the UI); it just isn't literally the `sudo systemctl` command,
since that one can't work from inside the app as currently provisioned.

"Requires Restart" detection: `common.dashboard_needs_restart(start_time)`
compares the process's start time against the mtimes of `app/dashboard.py`,
`app/common.py`, `app/templates/*`, and `app/static/*` — if any changed
after the process started, Flask (no autoreload, `debug=False`) is still
serving stale code/templates.

Files changed: `app/dashboard.py` (new `/api/admin/status` and
`/api/admin/restart` routes, `START_TIME`), `app/common.py`
(`dashboard_needs_restart`), `app/templates/index.html` (Admin tab UI +
polling JS).

**Tested live**, per CLAUDE.md's instruction not to claim a template/backend
fix as done without actually forcing a restart and verifying: restarted the
service via `kill -9` to pick up the new code, then exercised the new
`/api/admin/status` and `/api/admin/restart` endpoints directly with `curl`
— confirmed `needs_restart` correctly flips to `true` after touching a
watched file and back to `false` after a restart, and confirmed
`POST /api/admin/restart` actually kills and relaunches the process (new PID
each time, service stays `active`). Left the service running on the new code
afterward.

---

## Original request 1 (verbatim)

READY

Open a simple text editer for the request if the name is clicked

---

## Original request 2 (verbatim)

READY

Add an Admin tab that shows the status of the service.

Status: Running/Requires Restart/Restarting
A button below to restart

it runs the following when a request asks for it.

sudo systemctl restart bdraigui-dashboard


Mae the Admin tab change to a bright colour when it needs a restart
