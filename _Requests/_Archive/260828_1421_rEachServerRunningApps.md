# Each server: "running apps" home page (srvhome) — DONE / live

**Asked:** each server should have a home page showing which of its apps
are running plus a history of updates (version, timestamp, commit title +
description). Start with BdRPiSrvAMI. Update the docs. Later follow-ups:
colour-code it; document how the unattended session should hand back SSH
/ action steps; run `install.sh`.

**Outcome: built, deployed, and live on the Pi.**

## What was built

`srvhome` — a small standalone Flask app, one per server. Canonical
source version-controlled at `BdRDev/fleet/srvhome/`, deployed to
`~/projects/BdRPiAMI/srvhome/` on the Pi.

- One tile per hosted app (PlanBdRad, BdRAMAssist — scope "as per the
  Ecosystem 2 table"; BdRImpSys is an empty repo, skipped).
- Deployed **version = 7-char short SHA** of the checked-out repo, shown
  under the app name.
- **History of updates** table: version / pull-time / commit subject /
  body. Fed by a `post-merge` git hook installed in each app repo on the
  Pi — every `git pull` records the pulled SHA + title + body + pull
  time into a local SQLite DB (`srvhome.db`). `install.sh` back-fills
  the last 30 commits so the table isn't empty on day one (those rows
  tagged "backfilled", dated by commit time).
- **Colour-coded** per `_Instructions/WebUI.md`: status-coloured tile
  left border (green running / red down / amber not-tracked / grey
  absent), the history row matching the live checkout highlighted green
  and tagged "live here", backfilled rows muted, footer colour legend.
- Live "running" status was **deferred** (Brad: "leave this for now,
  lets just get it working") — tiles show a neutral "not tracked" badge;
  hook point flagged at `app_state()` in `srvhome.py`.

## Deployment

- Code + DB + git hooks deployed to the Pi over SSH (Tailscale).
- `install.sh` run by Brad — user-crontab keepalive active, server up on
  `127.0.0.1:8610`, `/healthz` → `ok`.
- Nginx `/status/` route added by Brad (`nginx-snippet.conf` into the
  `listen 443` block, above `location /`). Verified live from the dev
  box: `https://10.10.10.20/status/` → 200, page renders with full
  history; `https://bdrpiami/status/` and `https://100.86.25.88/status/`
  (Tailscale) also 200. Supabase untouched on `/`.

## Hostname clarification (Brad's last note)

Brad reported `https://10.10.10.20/status/` worked but
`https://bdrpisrvami.local/status/` didn't. That's expected: the Pi's
hostname is still `bdrpiami`, so its mDNS name is `bdrpiami.local` —
`bdrpisrvami.local` will not resolve until the host + Tailscale rename to
`BdRPiSrvAMI` actually happens (already tracked as pending in
`~/projects/CLAUDE.md`). **Working URL today:
https://bdrpiami.local/status/** (from a machine with mDNS), or
`https://bdrpiami/status/` / the LAN IP from the dev box.

## Docs updated

- `fleet/srvhome/README.md`, `DEPLOY-STATUS.md` — the app + its deploy.
- `_Instructions/WebUI.md` — "Colour-code status" as a fleet-wide rule.
- `_Instructions/Requests.md` — new "How to write actions and questions
  back into a request file" section (Action block / Question block
  formats), referenced from `_Instructions/SSH.md` and
  `_Instructions/BdRDev.md`.
- `~/projects/CLAUDE.md` — srvhome entry under the Pi's fleet status.

---

## Original request (verbatim)

```
READY

https://10.10.10.20/status/           worked
https://bdrpisrvami.local/status/     didnt work




## Follow-up done (Claude, 2026-08-28 pm)

Three things you asked for on the last pass:

1. **"Update the Level 1 instructions for how to respond and request SSH
   commands"** — done. `_Instructions/Requests.md` now has a section
   *"How to write actions and questions back into a request file"*
   defining the two block formats below, verbatim, fleet-wide.
   `_Instructions/SSH.md` and `_Instructions/BdRDev.md` both point at it.
2. **"Id like it to be colour coded too"** — done and redeployed to the
   Pi. `srvhome` tiles now have a status-coloured left border (green
   running / red down / amber not-tracked / grey absent), the history
   row matching the SHA that's actually checked out is highlighted green
   and tagged *"live here"*, backfilled rows are muted, and there's a
   colour legend in the footer. Also written into
   `_Instructions/WebUI.md` as a fleet-wide rule ("Colour-code status").
3. **`install.sh`** — I can see you already ran it: the crontab
   keepalive is active and `srvhome` is up on `127.0.0.1:8610`
   (`/healthz` → `ok`). The colour-coded build is the one running now
   (old process killed, per-minute cron picked up the new file).

## One step still needs you — the Nginx route (sudo)

`https://bdrpiami.local/status/` currently returns Supabase's `401`
because the `/status/` location block isn't in the site config yet, so
the request falls through to `location /`.

@@@ --- Action --- @@@

1. Route /status/ on the Pi to srvhome, so the page is reachable.

"Open the Pi's nginx site config"                          # on the Pi
sudo nano /etc/nginx/sites-available/bdrpiami

"Inside the `server { listen 443 ssl; ... }` block, ABOVE the existing
 `location / { proxy_pass http://127.0.0.1:8000; }`, paste the contents
 of ~/projects/BdRPiAMI/srvhome/nginx-snippet.conf — i.e. these lines:"
    location = /status { return 301 /status/; }
    location /status/ {
        proxy_pass http://127.0.0.1:8610/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

"Test the config and reload nginx"                         # on the Pi
sudo nginx -t
sudo systemctl reload nginx

"Confirm it's live (should print 200, then some HTML)"     # on the Pi
curl -s -o /dev/null -w '%{http_code}\n' -k https://127.0.0.1/status/
curl -s -k https://bdrpiami.local/status/ | head

@@@ ------------- @@@

Once that returns `200`, the feature is fully live at
**https://bdrpiami.local/status/** (Supabase stays untouched on `/`).
Flip this file to `READY` with a note if anything's off, otherwise
archive it.

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
```
