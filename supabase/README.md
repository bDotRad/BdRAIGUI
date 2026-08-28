# BdRDev Supabase

Fleet / ecosystem data for the Ecosystem, Fleet and Ecosystem-2 tabs used
to live only in `state/ecosystem.json` (seeded from
`app/common.py:DEFAULT_ECOSYSTEM`). This directory holds the Postgres
schema that data now belongs in, on the **self-hosted Supabase on
BdRPiAMI** (the Pi, Postgres 17).

## Files

| File | What |
|------|------|
| `migrations/20260828120000_fleet_schema.sql` | DDL: tables, indexes, `updated_at` triggers, RLS + policies, grants, the `fleet_ecosystem_json` view |
| `migrations/20260828120100_fleet_seed.sql` | Idempotent seed loading every row from `state/ecosystem.json` (2026-08-28) |
| `../.claude-status/sql_output.sql` | The two migrations concatenated with a header, for pasting into Studio by hand |

## Tables

| Table | Purpose |
|-------|---------|
| `servers` | One row per fleet machine (name, address, host type, OS/RAM/disk, git notes, `provisioned`, `dev_host`, `sort_order`). `software_freetext` keeps the diagram wording / "Other" column. |
| `software` | Canonical software/service catalogue. "SQL Lite" from the old JSON is normalised to `SQLite`. |
| `server_software` | M:N link (`server_id`, `software_id`, PK both). Source of the `claude` / `nginx` / `supabase` / `sqlite` booleans in the view. |
| `projects` | One row per Claude Code project. `exists_flag` is exposed as JSON key `exists`. |
| `project_agents` | Child of `projects`: agent names + `sort_order`. |
| `apps` | Deployed / planned apps. `server_id` is the resolved FK (nullable); `server_name` keeps the raw value. |
| `fleet_meta` | Single row (`id` forced to 1) holding the free-text `notes` blob. |

## How to apply

**Option A - Supabase CLI** (if/when this project adopts it):

```
supabase db push        # applies everything under migrations/
```

**Option B - by hand** (no CLI, no DB creds in the Claude session):
open Studio on the Pi -> SQL editor, paste the whole of
`.claude-status/sql_output.sql`, run. It is safe to re-run; the seed
upserts and never duplicates. If the new tables/view don't show on the
REST API immediately, run `notify pgrst, 'reload schema';` (the bundle
already does this at the end).

## The `fleet_ecosystem_json` view contract

`select ecosystem from public.fleet_ecosystem_json;` returns **exactly
one row, one `jsonb` column `ecosystem`**, shaped identically to
`common.load_ecosystem()`:

```jsonc
{
  "servers": [
    { "name": "", "tag": "", "address": "", "host": "", "os": "", "ram": "",
      "disk": "", "software": "",           // = servers.software_freetext
      "claude": false, "nginx": false,       // EXISTS in server_software
      "supabase": false, "sqlite": false,    //   joined to software.name
      "git": "", "provisioned": true, "dev_host": false }
  ],
  "projects": [ { "name": "", "exists": true, "agents": [] } ],
  "apps": [ { "name": "", "server": "", "tag": "", "web_address": "",
              "db": "", "planned": false } ],
  "notes": ""
}
```

Ordering of each array follows `sort_order` then `name`. `apps[].server`
is `server_name` if set, else the joined `servers.name`, else `""`.

The dashboard reads this view (server-side, with the service key).
`state/ecosystem.json` stays in place as a fallback cache for when the Pi
is unreachable - the app should fall back to it rather than erroring.

## RLS

Every table has RLS enabled. `service_role` gets full access (the
dashboard uses the service key server-side); `anon` and `authenticated`
get `SELECT` only. Writes from the Fleet tab go through `service_role`.
