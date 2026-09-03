WAITING RESPONSE

## Unattended pass 2026-09-04 — blocked, needs Brad

I picked this up after the flip to READY. Two things stop an unattended
session from finishing it:

1. **Step 1 was not applied.** The read path works (`source: supabase`),
   but every project row still holds the old free-text values —
   `status` is `deployed` across the board, `database` / `web_url` are
   the long free-text strings. So the "flip to READY once step 1 is
   done" precondition isn't actually met yet. Current live values from
   `curl localhost:8420/api/ecosystem`:

   | name            | database                     | status   | web_url                        |
   |-----------------|------------------------------|----------|--------------------------------|
   | BdRDev          | none (JSON state files)      | deployed | https://bdrpisrvdev.local/     |
   | BdRAMAssist     | none — feeds PlanBdRad's DB   | deployed | https://bdramassist.local/     |
   | PlanBdRad       | Supabase (Postgres)          | deployed | https://planbdrad.local/       |
   | BdRIS           | (empty)                      | planned  | (empty)                        |
   | BdRBirdDetector | none yet — cloud DB planned  | deployed | local network only, no fixed…  |
   | BdRDungeon      | Supabase (planned)           | planned  | not deployed yet               |

2. **`docker exec -i supabase-db psql` is blocked by the auto-mode
   classifier** for this session, so I can't run step 1, the write-path
   check, the view rebuild, or the drops from here. All of Part C is a
   Brad action now, not just `drop table`.

What I did do this pass (committed):

- Edited `supabase/DRAFT_fold_apps_into_projects.sql` so the Part B
  `create or replace view public.fleet_ecosystem_json` is already in its
  post-C form — the derived top-level `apps` object and the
  `projects[].agents` line are removed. Part C in that file is now
  uncommented and runnable, with `drop policy if exists` guards added so
  it's safe to re-run.

So the whole job is now: run the Action block below, top to bottom, on
the dev box. Step 3a is just "run the file I already edited".

@@@ --- Action --- @@@

1. Normalise the project rows to the status enum + real URLs.
   `# on the dev box`

"Normalise the project rows"
docker exec -i supabase-db psql -U postgres -v ON_ERROR_STOP=1 <<'SQL'
update public.projects set database='none',             status='live',     web_url='http://192.168.100.10:8420' where name='BdRDev';
update public.projects set database='shares:PlanBdRad', status='building', web_url=''                            where name='BdRAMAssist';
update public.projects set database='Supabase',         status='building', web_url='https://planbdrad.local'     where name='PlanBdRad';
update public.projects set database='none',             status='planned',  web_url=''                            where name='BdRIS';
update public.projects set database='none',             status='building', web_url=''                            where name='BdRBirdDetector';
update public.projects set database='Supabase',         status='planned',  web_url=''                            where name='BdRDungeon';
SQL

2. Confirm the read path carries the cleaned values (should show
   `source: supabase` and the normalised rows). `# on the dev box`

"Check the read path"
curl -s localhost:8420/api/ecosystem | python3 -m json.tool | grep -E 'source|runs_on|database|status'

3. Apply Part C — rebuild the view, then drop the old tables and add
   RLS/grants. Run only after step 2 looks right. `# on the dev box`

"Rebuild the view (Part B block, already edited to its post-C form) then run the Part C drops/RLS/grants"
docker exec -i supabase-db psql -U postgres -v ON_ERROR_STOP=1 -f ~/projects/BdRDev/supabase/DRAFT_fold_apps_into_projects.sql

   Note: that file also re-runs Part A (all `... if not exists` /
   `update ... where` / `on conflict` — safe) and the data-migration
   block, which now no-ops because `public.apps` / `public.project_agents`
   are dropped earlier in the same run. If you'd rather run just Part B
   + Part C, copy those two sections out and psql them directly.

4. Reload the Ecosystem tab in the browser — both the Servers and
   Projects grids should still load and round-trip through Edit → Save
   ("Saved to Supabase") → reload.

5. Flip this file back to READY (a fresh unattended session can then
   re-verify the read path and archive it), or archive it yourself with
   a one-line note on how it went.

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
