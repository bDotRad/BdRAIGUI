# srvhome: per-app "new version available" + one-click update

Processed 2026-08-30 by the Independent Claude session (unattended pass).

## What was asked

Add version-checking to each srvhome app tile on the Pi: a 5-min
background check for unpulled GitHub commits, a "Check" button to force
it, an "Update" button (when behind) that runs `git pull` + rebuild on
the box with progress/result on the tile, and a per-app version history
below the tile with a **committed date** column (the commit's own date)
next to the pull date and commit subject.

## What was found

The feature was already **built and committed** before this pass, by an
earlier session (commits `f74236c` "srvhome: per-app GitHub version
check + one-click update" and `6f3e041` "srvhome + update.sh: catch
stale builds, stop migrations freezing deploy"), and **deployed to the
Pi** — `srvhome.py`, `record_deploy.py`, `store.py` and
`~/projects/update.sh` on the Pi were already byte-identical to
canonical. The request file had just never been archived.

Delta this pass:

- **Re-synced the stale `srvhome/hooks/post-merge` template on the Pi.**
  It still had the pre-`6f3e041` version (no `--range ORIG_HEAD..HEAD`
  mode). The *installed* hooks in `~/projects/PlanBdRad/.git/hooks/` and
  `~/projects/BdRAMAssist/.git/hooks/` were already the current version,
  so history recording was fine; the template was just a landmine for a
  future `install.sh` re-run. Now all three match (`7c2c8f0b…`).
- Updated `fleet/srvhome/DEPLOY-STATUS.md` and `fleet/srvhome/README.md`
  to document the feature and record the deploy.

## How it ended up covering the ask

- **5-min check** → background thread, `git fetch` per app, holds
  `{behind, remote_sha, last_checked, error}` in memory. Interval was
  changed to **15 min** (`CHECK_INTERVAL_S = 900`) per a later Brad
  preference noted in `6f3e041`.
- **Check button** → `POST /api/check {app?}`, plus a "check all now"
  link in the section header.
- **Update button** → `POST /api/update {app}`, per-app lock, shells out
  to `~/projects/update.sh <app>` (the existing pull + apply-new-
  migrations + rebuild script — reused, not reimplemented). Combined
  output captured, shown in a `<details>` on the tile; page reloads on
  success.
- **Committed-date column** → `record_deploy.py` already captures
  `committed_at` (`git show -s --format=%cI`); every Pi history row has
  it, so no back-fill was needed. History table reshaped to
  `committed | pulled | commit`.
- **Stale-bundle detection** (from `6f3e041`, beyond the original ask) →
  `rebuild_needed` compares `git HEAD` to `app/dist/build-info.json`,
  surfacing a bundle that a no-op pull left stale (the real
  BdRAMAssist-served-3-commits-old-for-8h incident that prompted it).
- `update.sh` gained a migration ledger (`public._srvhome_migrations`)
  so an already-applied migration no longer freezes the deploy.

## Verified (2026-08-30, live on the Pi)

`curl localhost:8610/api/state` — checker running, `last_checked` fresh
(within the 15-min window); PlanBdRad and BdRAMAssist both `behind: 0`,
`built_sha == head_sha`, `rebuild_needed: false`, no errors; history
rows carry populated `committed_at`. `srvhome` serves 200 on
`127.0.0.1:8610`.

## Left for Brad — @@@ --- Action --- @@@

**The srvhome page is currently unreachable over the web.**
`https://<pi>/status/` returns **401** on every path tested (localhost,
`bdrpiami`, `bdrpiami.local`) — the `/status/` route in the Pi's nginx
site config has regressed since it was verified working 2026-08-28, so
requests fall through to Supabase's auth on `/`. srvhome itself is
healthy on `:8610`; only the nginx route is broken.

On the Pi, with sudo:

1. Check the `listen 443` server block of the Pi's nginx site config for
   the `location /status/ { … }` block from
   `~/projects/BdRPiAMI/srvhome/nginx-snippet.conf`. It's either missing
   or being shadowed by a broader `location /` proxy to Supabase.
2. Restore it (it must sort before / be more specific than the Supabase
   `location /`), then `sudo nginx -t && sudo nginx -s reload`.
3. Verify: `curl -sk https://localhost/status/ -o /dev/null -w '%{http_code}\n'`
   should be `200`.

This couldn't be diagnosed from the dev box — no sudo, and
`/etc/nginx/` isn't readable there.

@@@ --------------- @@@

---

## Original request (verbatim)

```
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
```
