# srvhome on BdRPiSrvAMI — deploy status (updated 2026-08-28 pm)

Built for request `rEach server running apps`. First target: the Pi.

## Done

- Code deployed to `~/projects/BdRPiAMI/srvhome/` on the Pi.
- Deploy DB `srvhome.db` back-filled from `git log`:
  PlanBdRad (23 commits), BdRAMAssist (17 commits).
- `post-merge` hook installed in `~/projects/PlanBdRad/.git/hooks/` and
  `~/projects/BdRAMAssist/.git/hooks/` — every future `git pull` on the
  Pi records the pulled version into `srvhome.db`.
- **`install.sh` run by Brad** — user-crontab keepalive active
  (`@reboot` + per-minute `run.sh`); server running on `127.0.0.1:8610`,
  `/healthz` → `ok`.
- **Colour-coding added** (request follow-up) and redeployed to the Pi:
  tiles carry a status-coloured left border (green running / red down /
  amber not-tracked / grey absent), the history row whose SHA matches
  the currently-deployed checkout is highlighted green with a "live
  here" tag, backfilled rows are muted, and the footer has a colour
  legend. Old process killed so the per-minute cron picked up the new
  code; verified rendering on the Pi.

## Nginx route — DONE (Brad, 2026-08-28)

The `nginx-snippet.conf` block is in the `listen 443` server block of
the Pi's site config. Verified live from the dev box:

```
https://10.10.10.20/status/    → 200   (page renders, full history)
https://bdrpiami/status/       → 200
https://100.86.25.88/status/   → 200   (Tailscale)
```

Supabase stays on `/`, untouched.

### Hostname note

`https://bdrpisrvami.local/status/` does **not** work, and won't until
the Pi is actually renamed. The box's hostname is still `bdrpiami`, so
its mDNS name is `bdrpiami.local`. `BdRPiSrvAMI` is only the canonical
name in the docs — the host + Tailscale rename is still pending (tracked
in `~/projects/CLAUDE.md`). Working URL today from a machine with mDNS
(Brad's desktop/laptop): **https://bdrpiami.local/status/**. From this
dev box (no mDNS resolver): `https://bdrpiami/status/` or the LAN IP.

If you'd rather use systemd than the crontab keepalive:
`sudo cp srvhome.service /etc/systemd/system/ && sudo systemctl enable
--now srvhome`, then delete the two `srvhome/run.sh` lines from
`crontab -e`.

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
