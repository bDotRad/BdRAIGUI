WAITING RESPONSE

## Built & deployed — 2 manual steps left for you (Claude, 2026-08-28 ~19:00)

`srvhome` is written, deployed to the Pi, tested working. Canonical
source: `BdRDev/fleet/srvhome/` (see its `README.md` + `DEPLOY-STATUS.md`).

**Done unattended over SSH (LAN `bdr@10.10.10.20`, key
`bdrdev_to_bdrpiamiserver` — the config comment saying that address is
unroutable is wrong):**
- code in `~/projects/BdRPiAMI/srvhome/` on the Pi
- deploy-history DB back-filled from `git log` (PlanBdRad 23, BdRAMAssist 17)
- `post-merge` git hook installed in both app repos — every future
  `git pull` on the Pi records the pulled 7-char SHA + title + body +
  pull-time into `srvhome.db`
- verified: `/healthz` ok, page + `/api/state` render with full history

**You need to run (my auto-mode classifier blocks starting a daemon on a
remote box, and all sudo):**

1. `cd ~/projects/BdRPiAMI/srvhome && ./install.sh` — idempotent;
   re-seeds, re-installs hooks, adds a user-crontab keepalive, starts it.
2. Add the `nginx-snippet.conf` block to
   `/etc/nginx/sites-available/bdrpiami` (in the `listen 443` block,
   above `location /`), then `sudo nginx -t && sudo systemctl reload nginx`.

Then it's live at **https://bdrpiami.local/status/** (Supabase stays on
`/`, untouched).

**Decisions I made (override in the file if you disagree):** page lives
on the Pi; live "running" status left as a neutral "not tracked" badge
per your answer #2 (hook point flagged in `srvhome.py`); scope =
PlanBdRad + BdRAMAssist (`apps.json`); sits alongside the Ecosystem tabs,
doesn't replace them.

Flip back to `READY` (or archive) once nginx is wired, or with notes if
you want changes.

---

Id like each server running apps to have a home page that shows the status of them and a history of updates.

So tiles is fine.
Whether its runnning at the moment.
A history of updates so the Version, Timestamp, commit title and description.

Start by making one for BdRPiSrvAMI

Make sure you update any documentation.

---

## Blocked — need decisions before building (added by Claude 2026-08-28 12:55)

This is a sizeable new feature with a few architecture calls I can't make
for you. Answer inline (edit each `A:` line) and flip the first line back
to `READY`.

**1. Where does this "home page" live and who serves it?**
  - (a) A new tab / section in the **BdRDev dashboard** (this app), one
    card per server, drill into a server to see its apps. Everything
    stays in one place; BdRDev already has the fleet data.
  - (b) A standalone page served **on each server itself** (e.g.
    `https://bdrpiami.local/` on the Pi), so hitting the box shows you
    what it's running. Needs a small app deployed per server.
  - (c) Both — dashboard aggregates, each server also self-reports.
  A: b The home page lives on the server...so BdRPiSrvAMI.....

**2. How should "running at the moment" be determined?**
  BdRDev runs on the dev box. Right now it **cannot reach the Pi at all**
  (the Ecosystem tab shows "Supabase unreachable"). To show live status
  it needs a reliable channel:
  - (a) SSH from BdRDev to each server and run `systemctl is-active
    <unit>` — needs an SSH key from the dev box to each server and a
    known list of systemd unit names per app.
  - (b) An HTTP healthcheck — BdRDev GETs a known URL per app and checks
    for 200. Needs each app to expose a health endpoint and be reachable
    from the dev box (Tailscale?).
  - (c) Each server pushes its own status to a shared store (Supabase
    table / a JSON endpoint) on a timer; the page just reads that.
  A: Leave this for now, lets just get it working.

**3. Where does the "history of updates" (version, timestamp, commit
   title + description) come from?**
  - (a) `git log` of the deployed repo on the server (BdRDev SSHes in and
    reads it). Requires SSH access + knowing the deploy path per app.
  - (b) A deploy step writes a record (to Supabase / a JSON file) every
    time an app is updated on a server — nothing exists that does this
    today; it'd need building as part of this.
  - (c) Read from GitHub's API (commits on the repo) — but that's "latest
    on the branch", not "what's actually deployed on that box".
  A: Git Log will do. Cant it get it when it does a pull? So it puts an entry into its own DB when it pulled that version.

**4. What is "Version"?**
  A git tag? A short commit SHA? A `VERSION` file in each repo? A
  `pyproject`/`package.json` version? None of the fleet apps seem to
  carry an explicit version string today.
  A: the 7 char code for the version that is under the title.

**5. Scope of "each server running apps".** Per `state/ecosystem.json` /
   CLAUDE.md the apps-per-server picture is:
  - **BdRPiSrvAMI** (`bdrpiami`, Tailscale `100.86.25.88`) — PlanBdRad
    (running), BdRAMAssist (repo cloned, not confirmed running as a
    service). This is the one you want first.
  - **BdRVSrvDev** (this box) — BdRDev dashboard + scheduler.
  - **BdRSrvDungeon**, **BdRBirdDetector** — not provisioned.
  Is "BdRPiSrvAMI first" just PlanBdRad + BdRAMAssist? And is the intent
  that this eventually replaces / merges with the existing **Ecosystem**
  / **Ecosystem 2** tabs, or sits alongside them as yet another view?
  A: As per the Ecosystem 2 table

**6. Does BdRDev have (or can it get) an SSH key to BdRPiSrvAMI?**
  Several of the options above hinge on this. `_Instructions/SSH.md` has
  the fleet key-naming convention but I don't know if a
  dev-box → Pi key is already deployed, and I can't create/authorise one
  unattended. If not, that's a prerequisite task for you.
  A: I dont know but yes it lives on the same local network
