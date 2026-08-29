WAITING RESPONSE

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

Answer:



??? --------------- ???
