WAITING RESPONSE

## Unattended pass 2026-09-04 — app + docs + migration SQL done; Brad runs the SQL + restart

All the code and doc changes are committed and pushed. What's left is the
one coupled step an unattended session can't do: run the schema migration
on the live Supabase (psql writes are classifier-blocked here) and
restart the dashboard (no sudo here; SIGKILL of a live dashboard for a
coupled change isn't a casual unattended move). Both are in the Action
block below — run them together, in order.

### Done this pass (commit on `master`)

- **`supabase/DRAFT_ecosystem_web_columns.sql`** — new migration, DRAFT
  convention (not in `migrations/`, run by hand like
  `DRAFT_fold_apps_PartBC_only.sql`). One `begin/commit`:
  rename `servers.web_url` → `local_url`, add `ts_url text`, rebuild
  `fleet_ecosystem_json` (server obj now `local_url` + `ts_url`, no
  `software`), **then** drop `software_freetext` (view recreated first so
  the drop isn't blocked by the dependency), then the
  `ecosystem-servers-tidied.csv` data load (renames keyed off the old
  name → safe to re-run), then `notify pgrst`.
- **`app/common.py`** — `_normalize_ecosystem` servers: `local_url`
  (falls back to old `web_url` key so stale caches migrate), `ts_url`,
  no `software`. `DEFAULT_ECOSYSTEM` rewritten to the CSV values
  (BdRPiSrvDev / BdRPiSrvAMI names, new addresses, `supabase` Y on the
  dev box, the two URLs). Dropped the unused `software` datalist option.
- **`app/fleet_db.py`** — `_write_all` writes `local_url` + `ts_url`,
  no `software_freetext`.
- **`app/templates/index.html`** — Servers grid: `Web` column → two
  columns `Local URL` + `Tailscale URL`; `ecoWebCell` takes a field
  name; blank-row + CSV-import seeds and `ECO_CSV_COLUMNS` updated.
  Projects grid `web_url` left alone (out of scope, per the ask).
- Docs: `README.md` ecosystem bullet, `supabase/DATA_MODEL.md` server
  table, `supabase/README.md` view contract + servers row.

FYI — index.html already had an **uncommitted CSV export/import feature**
in the working tree when this request landed (the request's own line
refs — 2161 / 2117 / 2252 — point at it). I built the column change on
top of it and it's in this commit. If that feature was mid-review and
shouldn't have shipped yet, say so.

Not touched: the free-text `notes` blob still names `BdRVSrvDev` /
`BdRPiAMI` — stale after the rename, but out of scope here.

@@@ --- Action (Brad, on the dev box) --- @@@

1. Apply the schema migration + data load to the live Supabase.

"Run the migration file inside the Postgres container"
docker exec -i supabase-db psql -U postgres -v ON_ERROR_STOP=1 < ~/projects/BdRDev/supabase/DRAFT_ecosystem_web_columns.sql

2. Restart the dashboard so the new app code loads (Flask has no autoreload).

"Pick up the app/common.py + app/fleet_db.py + app/templates/index.html change"
sudo systemctl restart bdrdev-dashboard

3. Verify the read path and the schema.

"Column renamed, new column present, old one gone"
docker exec -i supabase-db psql -U postgres -c "\d public.servers" | grep -E 'local_url|ts_url|software_freetext|web_url'

"API serves the new shape from Supabase"
curl -s localhost:8420/api/ecosystem | python3 -c "import json,sys; s=json.load(sys.stdin); print('source:', s['source']); [print(x['name'], x.get('local_url'), '|', x.get('ts_url')) for x in s['ecosystem']['servers']]"

   Expect: `\d` shows `local_url` + `ts_url`, no `software_freetext`, no
   `web_url`; API `source: supabase` with BdRPiSrvDev / BdRPiSrvAMI names
   and the two URL columns populated.

4. Reload the Ecosystem tab in the browser — Servers grid shows the
   `Local URL` + `Tailscale URL` columns, Edit → change a URL → Save →
   "Saved to Supabase" → reload sticks.

5. Flip this file's first line back to `READY` (note anything that
   failed) — a fresh unattended session will re-verify and archive it.

@@@ ------------- @@@

---

## Original request (verbatim)

READY

# Ecosystem: split web access into Local + Tailscale, drop `software` column

## Ask

Rework the **servers** side of the fleet/ecosystem data model so it records
web access as two fields instead of one, and drop a column that's now
redundant:

| Current field | Change |
|---|---|
| `web_url` | rename to **`local_url`** (LAN / mDNS `*.local` address) |
| *(new)* | add **`ts_url`** — the Tailscale front-door URL (`https://<node>.tail0ed3f6.ts.net[:port]`), blank where the box isn't on the tailnet or `tailscale serve` isn't set up yet |
| `software` | **remove** — the `claude` / `nginx` / `supabase` / `sqlite` booleans already cover "what runs here", and the free-text column had drifted |

Keep everything else (name, tag, address, tailscale IP, host, os, ram,
disk, the four software booleans, git, provisioned, dev_host).

Projects table: out of scope for now — leave its `web_url` alone unless
touching it is unavoidable, in which case call it out rather than
silently renaming.

## Where this touches

- `supabase/migrations/` — new migration: rename `web_url`→`local_url`,
  add `ts_url text`, drop `software`; update the `public.fleet_ecosystem_json`
  view to match. Run against the self-hosted Supabase on BdRPiSrvAMI.
- `app/fleet_db.py` — any column list / row mapping that names `web_url`
  or `software`.
- `app/common.py` — `DEFAULT_ECOSYSTEM` seed (the checked-in fallback)
  and `state/ecosystem.json` warm-cache shape.
- `app/templates/index.html` — Fleet tab editor field list (~line 2161),
  the blank-row templates (~2117, ~2252), and the Ecosystem 2 renderers
  (`ecoWebCell` / server + project rows, ~1907, ~1980, ~2016). The
  server web cell should show/edit `local_url` and `ts_url` as two
  columns; `ts_url` renders as a link the same way `web_url` did.
- Docs: README's "Ecosystem / fleet data" bullet, `supabase/DATA_MODEL.md`.

## Data to load at the same time

`ecosystem-servers-tidied.csv` in this folder is the corrected server
data — apply these values as part of the change:

- `BdRVSrvDev` → **`BdRPiSrvDev`**, address `192.168.100.10` →
  **`10.10.8.11`**, host `VM` → **`Raspberry Pi`**, `supabase` N → **Y**
  (Supabase now runs on this box on `127.0.0.1:8000`), `ts_url` =
  `https://bdrpisrvdev.tail0ed3f6.ts.net`, `local_url` =
  `https://bdrpisrvdev.local`
- `BdRPiAMI` → **`BdRPiSrvAMI`** (matches its Tailscale node
  `bdrpisrvami` and the nginx configs), `local_url` =
  `https://bdrpiami.local`, `ts_url` blank (`tailscale serve` not set up
  there yet — a bare tailnet name hits a password-protected default
  vhost)
- `BdRSrvDungeon` — not provisioned, both URLs blank
- `BdRBirdDetector` — LAN only, not on the tailnet: `local_url` =
  `http://bdrbirddetector.local` (plain http, no TLS on that box),
  `ts_url` blank

## Notes / context

- The Tailscale front door on `BdRPiSrvDev` is `tailscale serve`, not
  nginx: one MagicDNS hostname, one HTTPS port per app —
  `:443` dashboard, `:8443` CloudCLI, `:8000` Supabase. nginx there is
  bound LAN-only. See `BdRVSrvDev/scripts/tailnet-frontdoor.sh` and
  `BdRVSrvDev/CLOUDCLI.md`. The `ts_url` column only captures the
  primary per-server URL; per-app tailnet ports aren't modelled here.
- This project is in its own scheduler rotation, and the dashboard must
  be restarted (Brad's `sudo systemctl restart bdrdev-dashboard`, or a
  SIGKILL) to pick up `index.html` / `*.py` changes — verify via `curl`
  before calling it done.
