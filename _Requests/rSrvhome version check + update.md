READY

# srvhome: "new version available" + one-click update per app

From Brad, 2026-08-29 (relayed via the Independent Claude session).

## What Brad wants

This runs on **the server that hosts the apps** (BdRPiSrvAMI = the Pi).
That box already serves the srvhome dashboard at `https://<host>/status/`
with one tile per hosted app — this adds version-checking to each tile.

Per app tile:

1. **Background check every ~5 min** — does GitHub have commits the box
   hasn't pulled? If so, the tile says "new version available".
2. **A "Check" button** — force that check now instead of waiting.
3. **An "Update" button** — appears only when behind. Click it →
   `git pull` + rebuild on the box. Tile shows progress and the result.
4. **Version history, listed below the tile** — one row per version this
   box has run, newest first, three columns:
   - **committed** — the commit's own date (git author/committer date of
     that SHA), not when it was pulled
   - **pulled** — when this box pulled/deployed it
   - **commit text** — the commit subject (first line; full message on
     hover/expand is a nice-to-have)

## Where

Canonical source: `BdRDev/fleet/srvhome/` (`srvhome.py` + `store.py` +
`record_deploy.py`), deployed to `~/projects/BdRPiAMI/srvhome/` on the Pi.
Pure stdlib HTTP server, no Flask. It already has: app tiles with the
deployed 7-char SHA, **a deploy-history list per app** written by each
repo's `post-merge` git hook (`record_deploy.py` → `srvhome.db`: SHA,
commit title, description, `recorded_at`), a `POST /api/chat` route with
a single-flight lock.

So the history feature is **mostly there** — the tile already lists past
versions with commit title + pulled date. What's missing is the
**committed date** column: `record_deploy.py` needs to also capture
`git show -s --format=%cI <sha>` (or `%aI`) when it records a pull, and
back-fill it for existing rows from `git log`. Then the tile renders the
3-column table.

## Implementation notes

### Backend (`srvhome.py`)

- **Checker thread:** every 5 min, for each app in `apps.json`:
  `git -C <path> fetch --quiet` then compare
  `git rev-parse HEAD` vs `git rev-parse @{u}` → `behind` count +
  `remote_sha` + `last_checked` (ISO). Hold in memory; optionally
  persist last result to `srvhome.db` so a restart isn't blank.
  `git fetch` uses the box's existing read-only HTTPS PAT — no new auth.
- **`POST /api/check`** (optional `{app}`, else all) — run the fetch now,
  return the fresh state.
- **`POST /api/update` `{app}`** — take the single-flight lock (reuse the
  chat lock pattern, or a per-app lock), then:
  `git -C <path> pull --ff-only` → if that changed HEAD, run
  `<path>/build.sh`. Capture combined stdout/stderr; store
  `{ok, started_at, finished_at, sha_before, sha_after, output_tail}`.
  The `post-merge` hook already records the deploy to `srvhome.db`.
- **`GET /api/state`** — extend each app object with
  `{behind, remote_sha, last_checked, updating, last_update_result}`,
  and add `committed_at` to each history row.
- **`record_deploy.py` + `store.py`:** add a `committed_at` column to the
  deploy-history table (ISO 8601). Populate it from
  `git show -s --format=%cI <sha>` at record time; a one-time back-fill
  loop over existing rows (look each SHA up with `git log`) so old
  history isn't blank. `git fetch` in the checker also makes older
  commits resolvable.

### Frontend (the tile HTML in `srvhome.py`)

- Status pill per tile: green "up to date" / amber "N behind — update
  available" / blue "updating…" / red "update failed (see output)".
- "Check" button → `POST /api/check`, refresh the tile.
- "Update" button — only when `behind > 0`. Disable while `updating`.
  Show the captured `output_tail` in a `<details>` on completion.
- **History table below each tile**, newest first:
  `committed | pulled | commit text`. The tile already renders a history
  list — reshape it to these 3 columns and add the committed date.
- Poll `/api/state` every ~15 s (the page already refreshes facts) so a
  running update and the 5-min checker both surface without a manual
  reload.

### Gotchas

- **Node/PATH:** `build.sh` calls `npm`. srvhome runs from `run.sh` via
  cron — its `PATH` must include `~/.local/bin` (the nvm node 22 shims:
  `~/.local/bin/{node,npm,npx}` symlinks exist) or call an absolute
  node. Check `run.sh` / `srvhome.service`.
- **PlanBdRad `build.sh`** also does
  `"$PYSERVICE/.venv/bin/pip" install …` and `set -e` — the venv
  doesn't exist yet, so a plain `build.sh` will exit non-zero *after*
  writing `dist/`. Either call `build.sh -nr` from srvhome, or make
  `build.sh` skip the pyservice step gracefully when `.venv` is absent
  (better — do this as part of this request).
- **Failed build → half-written `dist/`:** `vite build` clears `outDir`
  first. A mid-build failure can leave the app broken. Nice-to-have:
  build into a temp dir and only swap on success. At minimum, surface
  the failure loudly in the tile and keep the "Update" button available
  to retry.
- **`git pull --ff-only`** so a diverged local checkout fails safely
  rather than creating a merge commit. If it fails, show that.
- Keep the checker cheap: `fetch` only (no `pull`), and skip apps whose
  `path` isn't a git repo.

## Nice-to-have (only if quick)

A global "Check all" button in the header, and a small "last checked
Nm ago" line so it's obvious the 5-min loop is alive.

---

## Note: the manual version already exists

`BdRDev/fleet/update.sh` (deployed to `~/projects/update.sh` on the Pi,
2026-08-29) does the pull + apply-new-migrations + rebuild for one app or
all. The dashboard "Update" button is essentially this per app, triggered
from the web UI with the output captured back to the tile. Reuse its
logic (esp. "apply only the `supabase/migrations/*.sql` that this pull
added, oldest first" and "build `app/` directly, not via `build.sh`").
