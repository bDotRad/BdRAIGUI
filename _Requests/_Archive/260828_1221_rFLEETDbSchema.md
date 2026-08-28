# rFLEET-db-schema — fleet/ecosystem data → Supabase

**Processed:** 2026-08-28 12:21
**Outcome:** Schema + app wiring built and committed. **Two manual steps
left for Brad** (no way to do them from an unattended session on this
host): run the SQL on the Pi's Supabase, and set 3 env vars +
restart the dashboard. Until then the dashboard runs exactly as before,
on `state/ecosystem.json` (the code falls back cleanly when Supabase is
unconfigured).

## What was asked

Brad flipped the earlier `WAITING RESPONSE` file to `READY` with:
"I dont want to use json... i want to use supabase. Get an agent to build
the supabase up and then get the web agent to update the page. go hard,
dont ask me anything just do it. i will look at the end."

So the 4 blocking questions in the file were answered by decision rather
than asking:

1. **Which Supabase?** The self-hosted one on BdRPiAMI. App connects out
   to it via env vars (`SUPABASE_URL` etc.) that Brad fills in.
2. **Hard DB dependency?** No — `state/ecosystem.json` stays as a warm
   cache/fallback. Dashboard never errors when the Pi is down; it just
   serves the JSON and shows `source: local JSON`.
3. **Schema scope?** The whole ecosystem model (servers, software,
   apps, projects, agents, notes), not just servers+software.
4. **Migration tool?** Plain timestamped SQL files under
   `supabase/migrations/` (standard supabase-cli layout). Nothing
   existed; this establishes the pattern.

## What was done

### Schema (supabase-sql-expert agent)

- `supabase/migrations/20260828120000_fleet_schema.sql` — 7 tables:
  - `servers` — one row per machine (name unique, tag, address, host,
    os, ram, disk, `software_freetext`, `git_notes`, provisioned,
    dev_host, sort_order). Partial unique index: at most one
    `dev_host = true`.
  - `software` — canonical catalogue (Claude Code, Nginx, Supabase,
    SQLite, Scheduler, Firebase; "SQL Lite" normalised to "SQLite").
  - `server_software` — M:N link (server ↔ software). Brad's
    "ProjectSoftware" idea, applied to servers. The per-package Y/N
    columns in the UI are `EXISTS` checks against this.
  - `projects` — one row per Claude Code project (name unique,
    `exists_flag`, sort_order).
  - `project_agents` — child of projects; agent names + order.
  - `apps` — deployed/planned apps (name, `server_id` nullable FK,
    `server_name` raw, tag, web_address, db, planned, sort_order).
  - `fleet_meta` — single enforced row holding the free-text `notes`.
  - RLS on every table: `service_role` full, `anon`/`authenticated`
    SELECT-only. `updated_at` triggers.
  - **View `public.fleet_ecosystem_json`** — one row, one `jsonb`
    column `ecosystem`, shaped *exactly* like
    `common.load_ecosystem()`'s output, so the app needs no reshaping
    on read.
- `supabase/migrations/20260828120100_fleet_seed.sql` — idempotent seed
  of every row currently in `state/ecosystem.json`.
- `.claude-status/sql_output.sql` — schema + seed concatenated, for
  pasting into the Pi's Supabase SQL editor by hand (shows as the "SQL"
  badge on the BdRDev card). Safe to re-run.
- `supabase/README.md` — schema overview, how to apply, the view
  contract, RLS summary.

Not executed against a real Postgres — no DB/psql/credentials reachable
from this session (Tailscale SSH to the Pi needs interactive browser
auth). Verified by structural review only.

### App wiring (web-dev-expert agent)

- `app/fleet_db.py` (new) — PostgREST client over `requests` (no
  `supabase`/`psycopg2` module available, and can't add binary deps).
  `is_configured()`, `fetch_ecosystem()` → dict|None, `push_ecosystem()`
  → bool. 5s timeouts. Honours `SUPABASE_VERIFY_SSL=0` /
  `SUPABASE_CA_BUNDLE` for the Pi's self-signed cert. Read path hits the
  view; write path upserts the base tables with the service key and
  deletes rows dropped from the payload (only touches the 4 tracked
  `server_software` links, so SQL-seeded ones like Scheduler survive).
- `app/dashboard.py` — `/api/ecosystem` GET tries Supabase then falls
  back to `common.load_ecosystem()`; POST tries Supabase then always
  also writes the JSON cache. Both add `"source": "supabase" |
  "json-fallback"` (additive — existing keys unchanged).
- `app/templates/index.html` — muted source line on the Fleet and
  Ecosystem 2 tabs ("source: Supabase" / "source: local JSON (Supabase
  unreachable)").
- `requirements.txt` (new, repo root) — `Flask`, `requests`.
  `app/requirements.txt` gained `requests`. `requests 2.34.2` +
  deps installed into `venv/` (prebuilt cp314 wheels, no compiler).
- `systemd/bdrdev-dashboard.service` — commented-out
  `# Environment=SUPABASE_URL=…` lines showing where the config goes.
- `README.md` — rewrote the "Ecosystem / fleet data" bullet.

### Verified here

- `venv/bin/python3` import + Flask test client: `GET /api/ecosystem`
  → 200, `source: json-fallback`, 4 servers; `/` → 200, contains
  `renderEco2` and the source line.
- With no `SUPABASE_*` env and with a dead URL: falls back instantly,
  no error.

### NOT done — Brad's manual steps

1. **Run the SQL on the Pi.** Paste `.claude-status/sql_output.sql` (or
   `supabase/migrations/*` via `supabase db push`) into the self-hosted
   Supabase on BdRPiAMI. `notify pgrst, 'reload schema';` is included.
2. **Configure + restart the dashboard.** On
   `bdrdev-dashboard.service` add:
   - `SUPABASE_URL=https://bdrpiami.local`
   - `SUPABASE_SERVICE_KEY=<service-role JWT from ~/projects/BdRPiAMI/SECRETS.md on the Pi>`
   - `SUPABASE_VERIFY_SSL=0`
   then `sudo systemctl daemon-reload && sudo systemctl restart bdrdev-dashboard`.
   (A `kill -9` on the dashboard pid would also pick up the code, but
   auto-mode's classifier blocked that from this session — and it's a
   live-service outage regardless, so it's Brad's call.)
3. The write path (Fleet-tab Save → Supabase) has never run against a
   real Postgres. First live save is the real test.

Also still open (out of scope, flagged in the request): the real
fleet-wide rename (`BdRDev` host → `BdRVSrvDev`, SSH keys, systemd
units, nginx) — display-only in the data so far.

## Files touched

- `supabase/migrations/20260828120000_fleet_schema.sql` (new)
- `supabase/migrations/20260828120100_fleet_seed.sql` (new)
- `supabase/README.md` (new)
- `.claude-status/sql_output.sql` (new, gitignored — transient handoff)
- `app/fleet_db.py` (new)
- `app/dashboard.py`
- `app/templates/index.html`
- `app/common.py` (from the earlier Ecosystem-2 pass, not yet committed)
- `app/scheduler.py` (earlier pass — unattended-session note in SCAN_PROMPT)
- `_Instructions/SSH.md` (earlier pass — BdRPiAMI key row)
- `README.md`, `requirements.txt` (new), `app/requirements.txt`
- `systemd/bdrdev-dashboard.service`
- `.gitignore` (added `.claude-status/`)

This commit also carries the previously-archived-but-unpushed
"Ecosystem 2" work (`_Requests/_Archive/260828_rf FLEET/`).

---

## Original request (verbatim)

```
READY

I dont want to use json...i want to use supabas.

Get an agent to buil the supabase up and then get the web agent to update the page.


go hard, dont ask me anything just do it. i will look at the end.

I trust what you do. and will fix it after i jsut want to see something.


# Fleet data → Supabase (Projects / Software / ProjectSoftware schema)

Split off from the original `rFLEET` request (the Ecosystem-2 table UI
part of that is done and archived — see
`_Archive/260828_*_rFLEETEcosystem2.md`). This file tracks the remaining
piece: moving the fleet/ecosystem data out of `state/ecosystem.json`
into a real Supabase schema, per Brad's answer to Q2:

> I want yes no for each software so its easy for a human to scan …
> the actual DB can be set up differently with a table like
> ProjectSoftware with a Proj to SW ID link.
> Tables might be: Projects, Software (ID, Name, Description),
> ProjectSoftware (ProjectID, SoftwareID).
> I need the SQL Agent to provide a good quality well thought out
> schema, not just shit. Needs to be in supabase, not just json files.

## Why this is blocked (need answers)

BdRDev currently has **no database at all** — every bit of its state is
JSON files under `state/`, and the app has no Supabase client, no
connection string, no migrations dir. Standing up a DB for it is a real
architectural change, not a schema-only task. Before the SQL agent can
design anything usable:

1. **Which Supabase instance?** The only live Supabase in the fleet is
   the self-hosted one on BdRPiAMI (the Pi, `10.10.10.20`). Does BdRDev
   connect out to that, or is there a separate/cloud project for it?
   Need the project URL + a service/anon key (or where to find them).
   A: 

2. **Is the dashboard allowed a hard DB dependency?** The scheduler and
   dashboard currently run with zero external deps and survive the Pi
   being down. If fleet data moves to Supabase, the Ecosystem / Fleet /
   Ecosystem-2 tabs stop working whenever the Pi is unreachable. OK, or
   should `state/ecosystem.json` stay as a cache/fallback that the DB
   syncs into?
   A: 

3. **Scope of the schema** — just servers + software + the
   server↔software link (what the table needs)? Or the whole ecosystem
   model (servers, projects, project↔agent, apps, apps↔server, apps↔db)?
   The current JSON has all of that.
   A: 

4. **Migration mechanism** — is there a preferred migrations tool for
   this project (raw SQL files, supabase-cli, alembic, …)? Nothing
   exists yet to copy the pattern from.
   A: 

Once these are answered, flip this back to `READY` and it goes to the
Supabase SQL Expert agent for the schema + a migration, then the Fleet
tab / `/api/ecosystem` get rewired to read/write the DB (with the JSON
file kept per the answer to Q2).

## Separately: the fleet-wide rename (BdRVSrv… / BdRPiSrv…)

Brad's Q3 answer set a naming rule: VM hosts = `BdRVSrv…`, Raspberry Pi
hosts = `BdRPiSrv…`, and `BdRSrvDev` → `BdRVSrvDev`.

**Done so far (display-only):** `state/ecosystem.json` +
`DEFAULT_ECOSYSTEM` now call the dev box `BdRVSrvDev`, and every server
has a `host` field (VM / Raspberry Pi / Physical).

**Not done (needs its own careful pass — deliberately not bundled into a
"scan requests" run):** the actual machine hostname is still `BdRDev`;
SSH key filenames/comments (`bdrdev_*`, see `_Instructions/SSH.md` —
which already flags the app-name-vs-hostname question as unresolved),
`~/.ssh/config` Host aliases, systemd unit names, nginx server_name, and
the various docs (`CLAUDE.md`, `MIGRATION_REPORT.md`, `SSH.md`) all still
say `BdRDev` / `BdRSrvDev`. Renaming those ripples across every project
on the Pi and needs Brad present. Also undecided: what `BdRSrvDungeon`
becomes (`BdRVSrvDungeon`? not provisioned yet, host type not fixed).
```
