# rFix all of the web pages — deploy the Pi's apps

Archived 2026-08-30 09:30 AEST by the Independent Claude session, at
Brad's instruction ("close off the two processing requests"). The core
ask — get PlanBdRad and BdRAMAssist actually deployed and serving on the
Pi — is **done and verified live**. One follow-up (PlanBdRad pyservice)
is carried over below.

## Outcome: both apps deployed and serving on BdRPiSrvAMI

Verified read-only from BdRVSrvDev + the Pi, 2026-08-30 09:2x:

| URL | State |
|---|---|
| `https://planbdrad.local` | ✅ 200 — built SPA, `.env` → `https://planbdrad.local`, real data restored into the Pi's Postgres (91 tables). Same-origin `/rest\|auth\|…` proxy to Supabase Envoy. |
| `https://bdramassist.local` | ✅ 200 — built SPA (`<title>BdR AM Assist</title>`), `.env` → `https://bdramassist.local`, `staging` schema live (migrations 001–005), `PGRST_DB_SCHEMAS` += `staging`. |
| mDNS | `planbdrad.local` / `bdramassist.local` → `10.10.10.20` ✅ (avahi-publish units). |
| Supabase stack | 11 containers healthy. |
| TLS | 2-tier CA — `fleetCA.crt` root (trust once per device) + per-host leaf covering both app names. |

The apps were never "broken" — they had simply never been deployed to the
Pi (the setup docs still pointed at the decommissioned VM
`192.168.100.20`). This was a first-time deploy, done across several
sessions and finished in the Independent Claude session driven live by
Brad on 2026-08-29 (Brad ran the sudo / Docker-exec steps).

Commits from the work: PlanBdRad `480b680`, `87b772d` (vite.config cert
fix); BdRAMAssist `e5d92e7`; BdRDev `c3b33aa` (fleet data
`BdRPiAMI`→`BdRPiSrvAMI`, app URLs).

## Carried over — not done

1. **PlanBdRad `pyservice`** (the `/api/docx/` Word/PDF generator).
   Needs Brad's sudo on the Pi — step 11 of the action block below:
   ```
   cd ~/projects/PlanBdRad/pyservice
   python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
   sudo apt install -y libreoffice --no-install-recommends
   sudo cp ~/projects/PlanBdRad/systemd/planbdradpydoc.service /etc/systemd/system/
   sudo systemctl daemon-reload && sudo systemctl enable --now planbdradpydoc
   ```
   Until then `https://planbdrad.local/api/docx/*` 502s; the rest of the
   app works. If it should be tracked, it belongs in
   `PlanBdRad/_Requests/`.

2. **`bdrpiami.local` mDNS is now dead** (the on-box hostname rename to
   `BdRPiSrvAMI` broke it). Only affects reaching Supabase Studio by that
   name — the apps are same-origin so unaffected. Cut over to
   `bdrpisrvami.local` (Nginx `server_name` + cert SAN) — tracked in the
   root `CLAUDE.md` "Not yet renamed on the Pi" list.

3. **Uncommitted on the Pi's pull-only `BdRPiAMI` checkout:**
   `nginx/bdrpiami.conf`, `tls/gen-cert.sh`, `tls/fleetCA.crt` — need
   committing wherever that repo is authored (`tls/fleetCA.key` stays
   gitignored).

4. `_Requests/rSrvhome version check + update.md` (auto-deploy / "new
   version" button) and `BdRAMAssist/_Requests/rNormalization
   workbench.md` are separate open requests, left in place.

===========================================================================
ORIGINAL REQUEST (verbatim)
===========================================================================

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

(The file then accumulated five processing passes — sweep notes, a
12-step Pi-deploy action block, and a final "deploy done" status. Full
history is in git before commit d14ad39..<archive commit>.)
