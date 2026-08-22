# rGUIFiles — build the dashboard

**Asked:** simple web interface to view what's happening across
projects, toggle which projects are in the scan rotation, round-robin
scanning for updated files, a status log so updates are easy to see, and
(if a project has SQL to run, e.g. in Supabase) a copyable output
window. Example dashboard/scheduler files were dropped alongside the
request as a starting point, with explicit license to keep, dump, or
mix.

**Found:** the dropped example (`dashboard.py` + `scheduler.py` +
`index.html`, Flask + tmux/systemd) was solid and became the base. It
assumed a `requests/` (lowercase) folder per project, but the other real
projects on this Pi (`BdRBirdDetector`) actually use `_Requests/` with
the `READY`/`NOT READY` first-line convention from
`_Instructions/Requests.md` — the example didn't know about that
convention at all, so as shipped it would never have detected pending
work in any real project. Also the systemd unit files referenced user
`brad` / `/home/brad/...` rather than this machine's `bdr` /
`/home/bdr/...`.

**Done:**
- Kept the two-process architecture (`app/dashboard.py` web UI,
  `app/scheduler.py` always-on round-robin daemon), talking only through
  JSON files in `state/`.
- Added `app/common.py` — shared scanning/state logic so the dashboard's
  pending-count badge and the scheduler's wake trigger can't drift out
  of sync. Implements the real `_Requests/` convention: READY/NOT READY
  first-line gating, `x`-prefix ignore, `_`-prefix reserved for
  archive/meta folders.
- Added an activity log (`state/activity_log.jsonl`, scheduler-appended,
  capped ~500 lines) and a log panel in the UI — addresses "status log
  so it's easy to see when things have been updated".
- Added the SQL-output convention: a project drops
  `.claude-status/sql_output.txt`, the dashboard shows a purple **SQL**
  badge with a copy-to-clipboard modal and a clear button — addresses
  the Supabase SQL request.
- Documented the SQL-output convention in `_Instructions/BdRGUI.md`
  (the doc meant to be copied into other projects) alongside the
  existing `status.json` convention.
- Fixed the systemd unit files for this machine (`bdr` /
  `/home/bdr/...`), pinned `CLAUDE_LAUNCH_CMD` to the real `claude`
  binary path since systemd's `PATH` won't see `~/.local/bin`.
- Smoke-tested: venv setup (needed `sudo apt install python3-venv
  python3-pip` first — machine had neither), `/api/status`,
  `/api/selected`, `/api/log`, `/api/sql/<project>` (+ clear) via curl,
  and one live scheduler pass against a zero-pending project confirming
  it correctly stays idle/hibernating and does *not* spawn a tmux
  session when nothing's pending.

**Outcome:** built and working, not yet installed as systemd services —
that step needs `sudo` and was left for Brad to run when ready (see
top-level `README.md`). Example files and this writeup superseded the
originals in `rf GUI Files/`, which are archived alongside this summary.
