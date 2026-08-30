# srvhome — per-server "running apps" home page

A tiny status page that runs **on a fleet server** and shows, for every
app that server hosts:

- the **version deployed here right now** — the 7-char commit SHA, plus
  its commit title and branch;
- a **running badge** — deliberately neutral ("status not tracked") for
  now; live status was deferred in the request. Wire it up later in
  `app_state()` in `srvhome.py`;
- a **history of updates** — every version this box has pulled, with the
  deploy timestamp, commit title and description.

The page is **colour-coded** per the fleet WebUI standard: each tile has
a status-coloured left border (green = running, red = down, amber = not
tracked, grey = repo absent), the history row matching the SHA currently
checked out is highlighted green and tagged "live here", backfilled rows
are muted, and the footer carries a legend.

First deployment target: **BdRPiSrvAMI** (the Pi, `10.10.10.20` /
tailnet `bdrpiami`). Canonical source of these files lives in
`BdRDev/fleet/srvhome/`; the running copy on the Pi is
`~/projects/BdRPiAMI/srvhome/`.

## How history is collected

`git pull` runs the repo's `.git/hooks/post-merge` hook. `install.sh`
drops [`hooks/post-merge`](hooks/post-merge) into each app repo; on every
pull it calls `record_deploy.py`, which writes the new HEAD
(7-char SHA / title / body / commit date / **pull time**) into
`srvhome.db` (SQLite). Re-recording the same SHA is a no-op, so the
per-minute keepalive and manual re-runs never create duplicates.

`install.sh` also **back-fills** the last 30 commits per repo so the
history table isn't empty on day one (those rows are tagged
"backfilled" and dated by commit time, not pull time).

The page itself reads `git` live for the current HEAD and reads
`srvhome.db` for history — no daemon-side polling.

## Version checking & one-click update

A background thread runs `git fetch` for every app every ~15 min
(`CHECK_INTERVAL_S`) and holds `{behind, remote_sha, last_checked,
error}` in memory (in-memory by design — a restart just re-checks within
seconds). Each tile shows a status pill: "up to date" / "N behind —
update available" / "serving `<sha>` — rebuild needed" / "updating…" /
"last update failed".

- **Check** (per tile, plus "check all now" in the section header) →
  `POST /api/check {app?}` forces a fetch now.
- **Update / Rebuild** (only when behind or a stale `dist/`) →
  `POST /api/update {app}` takes a per-app lock and shells out to
  `~/projects/update.sh <app>` — the existing pull + apply-new-migrations
  + rebuild script, reused not reimplemented. Combined output is captured
  and shown in a `<details>` on the tile.
- `rebuild_needed` compares `git HEAD` to `app/dist/build-info.json`'s
  `sha` (each app's `vite.config.ts` writes that at build time), so a
  stale bundle after a no-op pull is visible.
- Tiles poll `/api/state` every 15 s so the checker and a running update
  both surface without a manual reload.

History rows carry `committed_at` (the commit's own author/committer
date) alongside the pull time; the table renders `committed | pulled |
commit`.

## Files

| file | what |
|---|---|
| `srvhome.py` | the HTTP server (stdlib only, binds `127.0.0.1:8610`) |
| `store.py` | SQLite schema + helpers for `deploys` |
| `record_deploy.py` | records a repo's HEAD into the DB (hook + `--backfill`) |
| `apps.json` | which apps this server hosts (`name` + repo `path`) |
| `srvhome.conf.json` | server display name, bind host/port, history limit |
| `hooks/post-merge` | the git hook `install.sh` copies into each app repo |
| `install.sh` | back-fill + install hooks + crontab keepalive (no sudo) |
| `run.sh` | idempotent starter used by the crontab |
| `srvhome.service` | optional systemd unit (needs sudo) |
| `nginx-snippet.conf` | the `/status/` route to add to nginx (needs sudo) |

## Deploy (on the Pi)

```bash
mkdir -p ~/projects/BdRPiAMI/srvhome
# copy these files there (rsync from the dev box, or git-archive), then:
cd ~/projects/BdRPiAMI/srvhome
./install.sh
curl -s http://127.0.0.1:8610/api/state | head
```

Then, with sudo (Brad), add the nginx route from `nginx-snippet.conf`
and reload — the page is then at **https://bdrpiami.local/status/**.

## Adding another server later

Copy the dir to that box, edit `apps.json` + `srvhome.conf.json`, run
`install.sh`, add the nginx route. Nothing here is Pi-specific except
those two config files.
