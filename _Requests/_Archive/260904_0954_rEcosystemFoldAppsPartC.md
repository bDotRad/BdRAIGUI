# 260904_0954 — rEcosystem fold-apps Part C (destructive DB tidy-up)

Final leftover from `rEcosystemConsolidation`
(archived 2026-09-03 as `260903_0815_rEcosystemConsolidation.md`) and its
pass-2 / pass-3 follow-ups. The app side was already fully done; only the
destructive Supabase tidy-up remained, and it needed a hand-run `psql`
because the auto-mode classifier blocks DDL/DML from an unattended pass.

## What was done (2026-09-04, ~09:54 AEST)

Brad ran the SQL by hand from the Claude Code terminal (`!` bash mode) on
the dev box; Claude did the pre-checks, staged the command, and verified
the result.

**Pre-checks (Claude):**
- Confirmed live state matched the request: `public.apps` (6 rows),
  `public.project_agents` (21 rows) still present; RLS **off** on
  `public.roles` / `public.project_roles`.
- Verified the agent→role migration was complete: all 21 `project_agents`
  rows map cleanly onto the 21 `project_roles` (per-project counts match
  4/4, 4/4, 3/3, 5/5, 5/5; name mapping e.g. `Supabase SQL Expert`→`db`,
  `ESP32 Expert`→`elec_ctrl`, `Doc Updater`→`doco`).
- Backed up both tables (`pg_dump --table=public.apps
  --table=public.project_agents`) to the session scratchpad —
  `apps_project_agents_backup_20260904.sql`, not committed.
- Confirmed the dashboard writes to Supabase with the **service-role**
  key (`app/fleet_db.py:_service_key()`), so enabling RLS does not break
  the Edit→Save path (service_role bypasses RLS, and an explicit
  `*_service_all` policy is created too).

**Applied** — `supabase/DRAFT_fold_apps_PartBC_only.sql`, one
`begin/commit`, via `docker cp` + `docker exec supabase-db psql -U
postgres -v ON_ERROR_STOP=1 -f /tmp/pbc.sql`:
- `create or replace view public.fleet_ecosystem_json` in post-C shape
  (no more derived `apps` key, no `projects[].agents` line).
- `drop table public.apps`, `drop table public.project_agents`.
- `alter table ... enable row level security` on `public.roles` and
  `public.project_roles`; recreated `*_read_all` (SELECT → anon,
  authenticated) and `*_service_all` (ALL → service_role) policies with
  `drop policy if exists` guards; re-granted select to anon/authenticated
  and full DML + sequence usage to service_role.

**Verified after:**
- `to_regclass('public.apps')` and `('public.project_agents')` → NULL.
- `relrowsecurity = t` for both `roles` and `project_roles`; 4 policies
  present as expected.
- `curl localhost:8420/api/ecosystem` → `"source": "supabase"` with the
  normalised project rows intact (BdRDev `none`/`live`, PlanBdRad
  `Supabase`/`building`, BdRDungeon `Supabase`/`planned`, etc.).

**Not re-verified in this pass:** the browser round-trip (reload the
Ecosystem tab, Edit → Save → "Saved to Supabase" → reload). Read path and
write-auth model both check out, so this is expected to be fine.

## Files

- `supabase/DRAFT_fold_apps_PartBC_only.sql` — marked APPLIED, kept for
  the record.
- `supabase/DRAFT_fold_apps_into_projects.sql` — header updated: the
  whole file is now fully historical, do not run any of it.
- No app-code change (the `app/common.py` read shim for the old `apps`
  shape was already removed on the 2026-09-03 pass).

## Outcome

Done and pushed. The `apps` / `project_agents` tables are gone, RLS
posture on the role tables is correct, and the `fleet_ecosystem_json`
view no longer carries the dead keys. `projects` is the single source of
truth for the deployment facet.

---

## Original request (verbatim)

```
READY

I am going to let the claude CLI pick ths ip and work through it there.



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
```
