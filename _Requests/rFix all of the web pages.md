READY

I dont know what you want.

I gave answers

Answer: 1 a, 2 i can, 3 get it to work. 4. Yes. Go for it just get it to a stage of working

Give me actions or close this,.

-----------------
bdrpisrvami isnt working. i have another claude on that server trying to fix it. work together.
the bdramassist isnt working.
planbdr prbobaly isnt.

do a sweep of all servers and projects and make sure if it needs supabase its set up. if it needs a we page....set it up. fix the exo system. this is becaoming too hard to do...it shouldnt be.

Use FIX STUFF sitting in projects on the BdRPISrvAMI server

---

## Sweep done — state, coordination note written, calls I need from you (Claude/BdRDev, 2026-08-29)

Sweep run from the dev box (dashboard API + SSH to the Pi over
`10.10.10.20`). I wrote my findings + a proposed division of labour into
`~/projects/FIX STUFF.md` on the Pi for the other Claude to pick up — it
was empty; it now has 72 lines. I did **not** change anything else on
the Pi (read-only checks only) — concurrent cross-machine edits with the
other session are exactly how this breaks.

### The headline: nothing is "broken" — the apps were never deployed to the Pi

Supabase on the Pi is **healthy** (11 containers up, REST reachable,
BdRDev's fleet schema live). What's missing is the deploy: PlanBdRad and
BdRAMAssist are cloned on the Pi but have no systemd unit, no port, no
nginx route, and their migrations have never run against the Pi's
Postgres. Their setup docs still target the **decommissioned** VM
(`192.168.100.20` / old `BdRSrvAMI`) — and per PlanBdRad's own
`VM_SETUP.md`, HTTPS was never finished there either.

| Thing | State |
|---|---|
| Pi self-hosted Supabase | ✅ healthy — not the problem |
| `https://bdrpiami.local/` | ⚠️ nginx `/` → Supabase Envoy (`:8000`) → Studio 401. No landing page, no app route. Only `/status/` → srvhome (`:8610`). |
| srvhome `:8610` | ~ `/status/` gave 200 but the port wasn't listening when I checked — flagged for the Pi Claude |
| PlanBdRad on Pi | ❌ cloned, not deployed (FastAPI `pyservice/main.py` + a frontend build; migrations never run) |
| BdRAMAssist on Pi | ❌ cloned, not deployed (Vite frontend; wants a `staging` schema + shared nginx that don't exist yet) |
| BdRDungeon / BdRBirdDetector | ❌ servers not provisioned / not tailnet — out of scope until hardware exists |
| BdRDev dashboard | ✅ working (`bdrdev.local` → `:8420`, Supabase-backed) |
| Setup docs | ❌ ~13 files in PlanBdRad + BdRAMAssist still reference `192.168.100.20` / `BdRSrvAMI` |

### The real work (a first-time deploy, not a fix)

- **A. Pick the Pi web layout** — Question 1. Every nginx file depends on it.
- **B. Deploy PlanBdRad to the Pi** — systemd `--user` unit for
  `pyservice`, frontend build, `.env` → Pi Supabase, run
  `supabase/migrations/*` on the Pi's Postgres, nginx route. Needs
  sudo + DDL — both walled off from an unattended dev-box session.
- **C. Deploy BdRAMAssist to the Pi** — frontend build, `staging`
  migrations, `PGRST_DB_SCHEMAS` append + PostgREST restart, nginx route.
- **D. Rewrite the stale server docs** in both repos to target the Pi —
  **BdRDev can do this now** (Question 4).
- **E. Update BdRDev's fleet data** (`BdRPiAMI` → canonical
  `BdRPiSrvAMI`, app web addresses) once B/C land — BdRDev can do this.

@@@ --- Action --- @@@

Nothing for BdRDev to run — blocked on the Questions below. The Pi-side
deploy shape (for you or the Pi's Claude) is written out in
`~/projects/FIX STUFF.md` on the Pi.

@@@ ------------- @@@

??? --- Question --- ???

**1. Pi web layout for `bdrpiami.local` + the apps:**
   a. **Per-app mDNS hostnames** (recommended) — `planbdrad.local`,
      `bdramassist.local` via `avahi-publish` → the Pi, nginx routes by
      `server_name`. Supabase stays on `bdrpiami.local`; srvhome stays
      the fleet index at `bdrpiami.local/status/`. Matches how
      `bdrpiami.local` already works; each app gets a clean root URL.
   b. **Sub-paths** — `bdrpiami.local/planbdrad/`, `/bdramassist/`,
      `/` redirects to `/status/`, Supabase Studio moves to `/studio/`.
      Needs app base-path rewrites.
   c. Something else.

**2. Who runs the Pi's sudo + migration steps?** BdRDev can't (no sudo
here; auto-mode blocks remote DDL). You / the Pi's Claude / add a Bash
permission rule for a future BdRDev pass?

**3. What is the other Pi Claude's current job?** App deploys (B/C), or
the `BdRPiAMI`→`BdRPiSrvAMI` rename / srvhome / nginx route? Tell me its
lane. **Default if unanswered: BdRDev stays off the Pi and only does
D + E.**

**4. Can BdRDev do D (doc rewrites) + E (fleet-data fix) now?** Yes/no —
and if yes, give me the Q1 layout so the new docs are correct.

Answer: 1 a, 2 i can, 3 get it to work. 4. Yes. Go for it just get it to a stage of working

??? --------------- ???

---

## [DEV] Everything BdRDev can do is done. Here is the exact action list. — 2026-08-29

**What "give me actions" means here:** the two apps have never been
deployed to the Pi. Nothing is corrupt — there is just no build, no
nginx route, and no schema in Postgres yet. The remaining work is one
first-time deploy. BdRDev cannot run it: it needs `sudo` on the Pi, and
this unattended session's safety classifier blocks *all* writes to a
remote host over SSH (it blocked even `git pull`). So it is written out
below as a single copy-paste sequence.

**BdRDev has already done (committed + pushed):**
- PlanBdRad `480b680`, BdRAMAssist `e5d92e7` — deploy docs + nginx /
  systemd / avahi configs re-targeted from the dead VM to the Pi, per
  layout **1a** (`planbdrad.local` / `bdramassist.local`).
- BdRDev `c3b33aa` — fleet data (`ecosystem.json` + `common.py`):
  `BdRPiAMI` → `BdRPiSrvAMI`, app URLs set (tagged "pending Pi deploy").
- `~/projects/FIX STUFF.md` on the Pi — `[DEV]` log entry for the Pi's
  Claude (its lane: cert regen + uncommenting the per-app nginx blocks
  in `nginx/bdrpiami.conf`, then `./build.sh` once Node exists).

**Verified Pi state (2026-08-29, read-only over SSH):** Supabase healthy
(11 containers). Node **not installed**. `PGRST_DB_SCHEMAS=public,graphql_public`.
Cert `~/projects/BdRPiAMI/tls/bdrpiami.local.crt` covers `bdrpiami*` /
`bdrpisrvami*` but **not** `planbdrad.local` / `bdramassist.local`. Both
repos on the Pi are behind (need `git pull`). No `app/.env` in either.

@@@ --- Action --- @@@

All steps run on the Pi. Connect first:

"from the dev box"
ssh -i ~/.ssh/bdrdev_to_bdrpiamiserver bdr@10.10.10.20

1. Pull the re-targeted configs (both repos are behind)

"get the new SERVER_SETUP / nginx / systemd files"
cd ~/projects/PlanBdRad && git pull --ff-only
cd ~/projects/BdRAMAssist && git pull --ff-only

2. Install Node 22 (needs sudo — apt's nodejs is v18, too old for Vite)

"add the NodeSource repo and install"
curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash -
sudo apt-get install -y nodejs
node -v

3. Write app/.env for both apps (pulls the anon key from the Supabase stack)

"one env file, same two values, for each app"
ANON=$(grep '^ANON_KEY=' ~/projects/supabase/docker/.env | cut -d= -f2-)
printf 'VITE_SUPABASE_URL=https://bdrpiami.local\nVITE_SUPABASE_ANON_KEY=%s\n' "$ANON" > ~/projects/PlanBdRad/app/.env
printf 'VITE_SUPABASE_URL=https://bdrpiami.local\nVITE_SUPABASE_ANON_KEY=%s\n' "$ANON" > ~/projects/BdRAMAssist/app/.env

4. Load the PlanBdRad schema into Postgres (rootless Docker — no sudo)

"full schema in one transaction, then the t000 lookup seed data, then the view"
docker exec -i supabase-db psql -U postgres -v ON_ERROR_STOP=1 < ~/projects/PlanBdRad/supabase/FRESH_INSTALL.sql
docker exec -i supabase-db psql -U postgres -v ON_ERROR_STOP=1 < ~/projects/PlanBdRad/supabase/population/run_all.sql
docker exec -i supabase-db psql -U postgres -v ON_ERROR_STOP=1 < ~/projects/PlanBdRad/supabase/views/v_pmi_step_items.sql

5. Load the BdRAMAssist schema (migrations 001–005, into the `staging` schema)

"apply each migration in order, stop on first error"
for f in ~/projects/BdRAMAssist/supabase/migrations/00{1,2,3,4,5}_*.sql; do echo "== $f =="; docker exec -i supabase-db psql -U postgres -v ON_ERROR_STOP=1 < "$f"; done

6. Expose the new schemas to the REST API and restart it

"append the four schemas, then restart just the PostgREST container"
cd ~/projects/supabase/docker
sed -i 's/^PGRST_DB_SCHEMAS=.*/PGRST_DB_SCHEMAS=public,graphql_public,t000,t100,t300,staging/' .env
docker compose restart rest

"verify both apps' tables answer (expect 200 twice)"
ANON=$(grep '^ANON_KEY=' .env | cut -d= -f2-)
curl -s -o /dev/null -w '%{http_code}\n' -H "apikey: $ANON" 'http://127.0.0.1:8000/rest/v1/t000_frequency?select=*&limit=1'
curl -s -o /dev/null -w '%{http_code}\n' -H "apikey: $ANON" 'http://127.0.0.1:8000/rest/v1/raw_import_batch?select=*&limit=1'

7. Regenerate the TLS cert with the two app hostnames added (no sudo)

"add planbdrad.local + bdramassist.local to the SAN list, then regenerate"
sed -i 's/DNS:bdrpisrvami,DNS:localhost/DNS:bdrpisrvami,DNS:planbdrad.local,DNS:bdramassist.local,DNS:localhost/' ~/projects/BdRPiAMI/tls/gen-cert.sh
bash ~/projects/BdRPiAMI/tls/gen-cert.sh

8. Build both frontends (needs step 2 + step 3 done first)

"first build for PlanBdRad skips the pyservice restart; BdRAMAssist has no backend"
cd ~/projects/PlanBdRad && ./build.sh -nr
cd ~/projects/BdRAMAssist && ./build.sh

9. Turn on the two per-app nginx vhosts and reload (needs sudo)

"in ~/projects/BdRPiAMI/nginx/bdrpiami.conf the PlanBdRad and BdRAMAssist"
"server{} blocks are present but commented out (lines ~73-121, each line"
"prefixed with '#'). Open the file and remove the leading '#' from the two"
"'server { ... }' blocks (leave the '# ---- ' banner comments as-is). Then:"
nano ~/projects/BdRPiAMI/nginx/bdrpiami.conf

"install the consolidated site + reload (this script wants root)"
sudo bash ~/projects/BdRPiAMI/nginx/deploy.sh

10. Publish the two mDNS names (needs sudo)

"install and start the avahi-publish units shipped in each repo"
sudo cp ~/projects/PlanBdRad/systemd/avahi-publish-planbdrad.service /etc/systemd/system/
sudo cp ~/projects/BdRAMAssist/systemd/avahi-publish-bdramassist.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now avahi-publish-planbdrad.service avahi-publish-bdramassist.service

11. PlanBdRad pyservice — the Word/PDF generator behind /api/docx/ (needs sudo)

"venv + headless LibreOffice + systemd unit"
cd ~/projects/PlanBdRad/pyservice
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
sudo apt install -y libreoffice --no-install-recommends
sudo cp ~/projects/PlanBdRad/systemd/planbdradpydoc.service /etc/systemd/system/
sudo systemctl daemon-reload && sudo systemctl enable --now planbdradpydoc

12. Verify

"each should return HTML / 200"
curl -k -H 'Host: planbdrad.local' https://127.0.0.1/ | head
curl -k -H 'Host: bdramassist.local' https://127.0.0.1/ | head
curl -k -H 'Host: planbdrad.local' https://127.0.0.1/api/docx/health

@@@ ------------- @@@

**Step 9's first `sed` is fragile** — it un-comments a line range in
`nginx/bdrpiami.conf`. Eyeball the file after running it (the two
`server { }` blocks for `planbdrad.local` and `bdramassist.local` should
be uncommented, nothing else). The Pi's own Claude can do step 7 + 9's
edit instead — that file is its lane — leaving you only `sudo bash
deploy.sh`. It's been told so in `FIX STUFF.md`.

Once this is done: flip this file to `READY` with a note (or archive it),
and BdRDev will switch the ecosystem "pending Pi deploy" tags to live.
If any step errors, paste the error under here and flip to `READY`.

??? --------------- ???
