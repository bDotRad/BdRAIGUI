WAITING RESPONSE

## Unattended pass 2026-09-04 (pass 3) — step 1 verified done; step 3 is a one-command Brad action, and the old step-3 command was WRONG

Good news since pass 2: **step 1 is applied.** The read path now returns
`source: supabase` with the normalised rows (verified both via
`curl localhost:8420/api/ecosystem` and a direct `select` on
`public.projects`):

   | name            | database         | status   | web_url                      |
   |-----------------|------------------|----------|------------------------------|
   | BdRDev          | none             | live     | http://192.168.100.10:8420   |
   | BdRAMAssist     | shares:PlanBdRad | building | (empty)                      |
   | PlanBdRad       | Supabase         | building | https://planbdrad.local      |
   | BdRIS           | none             | planned  | (empty)                      |
   | BdRBirdDetector | none             | building | (empty)                      |
   | BdRDungeon      | Supabase         | planned  | (empty)                      |

So steps 1 and 2 of the old Action block are **done**. Only step 3
(rebuild view + drop tables + RLS/grants) is left.

### Two blockers for finishing it unattended

1. **psql writes are still classifier-blocked.** Read-only `select`s go
   through (that's how I verified the above), but any
   `docker exec -i supabase-db psql ...` that runs DDL/DML — including
   `-f <file>` and heredocs — is denied by the auto-mode classifier.
   The `drop table` / `create or replace view` still needs Brad.

2. **The old step-3 command in the pass-2 Action block was wrong — do
   NOT run it.** It said to `psql -f DRAFT_fold_apps_into_projects.sql`
   (the whole file), with a note claiming Part A's data-migration block
   "no-ops because apps / project_agents are dropped earlier in the same
   run." That's backwards: in that file Part A (the `apps -> projects`
   UPDATE at lines ~81–104) runs **before** the Part C drops, so
   re-running the whole file would overwrite the step-1 normalised
   values with the old `apps` free-text (`database='none (JSON state
   files)'`, `status='deployed'`, etc.). `public.apps` still holds those
   old strings — confirmed this pass.

### What I did this pass (committed)

- Added **`supabase/DRAFT_fold_apps_PartBC_only.sql`** — Part B (the
  view rebuild, already in post-C form) + Part C (drops + RLS + grants),
  wrapped in a single `begin/commit`, with `drop policy if exists`
  guards. This is the *safe* subset to run — it does not touch the
  normalised rows.
- Added a warning header to `DRAFT_fold_apps_into_projects.sql` saying
  not to run the whole file again, pointing at the PartBC-only file.
- Backed up `apps` + `project_agents` data to the session scratchpad
  (`apps_project_agents_backup_20260904.sql`) — not committed; the
  agent data is already fully migrated into `project_roles` (all 5
  projects mapped, 0 unmapped agents, verified this pass).

@@@ --- Action (Brad, on the dev box) --- @@@

1. Run the safe Part B + Part C subset:

docker exec -i supabase-db psql -U postgres -v ON_ERROR_STOP=1 -f ~/projects/BdRDev/supabase/DRAFT_fold_apps_PartBC_only.sql

2. Sanity-check:

docker exec -i supabase-db psql -U postgres -c "select to_regclass('public.apps'), to_regclass('public.project_agents');"
docker exec -i supabase-db psql -U postgres -c "select relname, relrowsecurity from pg_class where relname in ('roles','project_roles');"
curl -s localhost:8420/api/ecosystem | python3 -m json.tool | grep -E 'source|\"status\"|\"database\"'

   Expect: both `to_regclass` NULL, both tables `relrowsecurity = t`,
   read path still `source: supabase` with the normalised rows.

3. Reload the Ecosystem tab — Servers + Projects grids should still load
   and round-trip Edit → Save ("Saved to Supabase") → reload.

4. Flip this file's first line back to `READY` — a fresh unattended
   session will re-verify and archive it.

@@@ ------------- @@@

--- original request below ---

Leftover from `rEcosystemConsolidation` (archived 2026-09-03 as
`260903_0815_rEcosystemConsolidation.md` — see there for full context).
The app side is fully done; only the destructive DB tidy-up is left, and
it needs Brad to run it by hand on the source-of-truth Supabase. Flip
this to `READY` once step 1 has been done (via the Ecosystem tab or the
SQL below) — an unattended pass can then verify the read path and do the
view rebuild, but it still won't `drop table` on the live DB, so step 3
stays a Brad action.

## Current gap (verified 2026-09-03)

- `public.apps` and `public.project_agents` still exist — unread by the
  app, unwritten. Just clutter now.
- `public.roles` / `public.project_roles` have grants but **RLS is off**
  → `anon` can INSERT/UPDATE/DELETE. Local-dev only, but wrong posture.
- `fleet_ecosystem_json` still builds the derived `apps` key and the
  `projects[].agents` line. Harmless (the dashboard's `_normalize_
  ecosystem` drops both), but they should come out with the tables.
- Project rows still hold the old free-text values: `database` like
  "none (JSON state files)", `web_url` like "not deployed yet" /
  "10.10.10.20" / "local network only, no fixed URL", every `status` =
  `deployed`.

Notes:
- `supabase/DRAFT_fold_apps_into_projects.sql` Part C holds the same
  block (now uncommented + runnable) plus the view-rebuild edit.
- The `app/common.py` read shim for the old `apps` shape was already
  removed on the 2026-09-03 pass, so nothing app-side depends on the old
  tables or view keys.
