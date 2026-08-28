# srvhome on BdRPiSrvAMI — deploy status (2026-08-28)

Built for request `rEach server running apps`. First target: the Pi.

## Done (by the unattended session, over SSH from the dev box)

- Code deployed to `~/projects/BdRPiAMI/srvhome/` on the Pi.
- Deploy DB `srvhome.db` back-filled from `git log`:
  PlanBdRad (23 commits), BdRAMAssist (17 commits).
- `post-merge` hook installed in `~/projects/PlanBdRad/.git/hooks/` and
  `~/projects/BdRAMAssist/.git/hooks/` — every future `git pull` on the
  Pi records the pulled version into `srvhome.db`.
- App verified working on the Pi (foreground run: `/healthz` ok,
  `/api/state` and the HTML page render with full history).

## Left for Brad — 2 steps (the unattended session's auto-mode
## classifier blocks starting a daemon on a remote box and all sudo)

**1. Start it + make it stay up (no sudo):**

```bash
cd ~/projects/BdRPiAMI/srvhome
./install.sh          # re-runs backfill (idempotent), re-installs hooks,
                      # adds a user-crontab keepalive, starts the server
curl -s http://127.0.0.1:8610/healthz     # -> ok
```

`install.sh` is safe to run repeatedly. If you'd rather use systemd than
the crontab keepalive: `sudo cp srvhome.service /etc/systemd/system/ &&
sudo systemctl enable --now srvhome`, then delete the two
`srvhome/run.sh` lines from `crontab -e`.

**2. Expose it through Nginx (needs sudo):** add the block from
`nginx-snippet.conf` into the `listen 443` server block of
`/etc/nginx/sites-available/bdrpiami`, above the existing
`location / { proxy_pass ... :8000; }`, then:

```bash
sudo nginx -t && sudo systemctl reload nginx
```

Page is then live at **https://bdrpiami.local/status/**
(Supabase stays on `https://bdrpiami.local/`, untouched).

## Design decisions made (flagged for review — see request answers)

- **Lives on the Pi** (answer #1) at `~/projects/BdRPiAMI/srvhome/`;
  canonical source is version-controlled in `BdRDev/fleet/srvhome/`.
- **Live "running" status deferred** (answer #2) — tiles show a neutral
  "status not tracked" badge. Hook point: `app_state()` in `srvhome.py`.
- **History from git log + a pull-time DB** (answer #3) — the post-merge
  hook writes each pulled version to `srvhome.db`; `install.sh`
  back-fills the last 30 commits so history isn't empty on day one
  (those rows tagged "backfilled", dated by commit time not pull time).
- **Version = 7-char short SHA** (answer #4).
- **Scope = PlanBdRad + BdRAMAssist** (answer #5, "as per the
  Ecosystem 2 table" — BdRIS/BdRImpSys is an empty repo, skipped). Edit
  `apps.json` to add more.
- **Sits alongside** the dashboard's Ecosystem / Ecosystem 2 tabs; does
  not replace them. It's a per-server page, not a fleet aggregator.
