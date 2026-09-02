NOT READY

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

@@@ --- Action (Brad) --- @@@

All on the dev box (BdRVSrvDev). `docker exec -i supabase-db psql -U
postgres` is the SQL shell — no sudo needed for the DB parts.

1. Normalise the project rows. Either do it in the browser — Ecosystem
   tab → Edit → fix the Projects grid → Save (status should read "Saved
   to Supabase"), reload, confirm it stuck (this also exercises the
   write path) — or run the equivalent SQL:

"Normalise the project rows to the status enum + real URLs"
docker exec -i supabase-db psql -U postgres -v ON_ERROR_STOP=1 <<'SQL'
update public.projects set database='none',             status='live',     web_url='http://192.168.100.10:8420' where name='BdRDev';
update public.projects set database='shares:PlanBdRad', status='building', web_url=''                            where name='BdRAMAssist';
update public.projects set database='Supabase',         status='building', web_url='https://planbdrad.local'     where name='PlanBdRad';
update public.projects set database='none',             status='planned',  web_url=''                            where name='BdRIS';
update public.projects set database='none',             status='building', web_url=''                            where name='BdRBirdDetector';
update public.projects set database='Supabase',         status='planned',  web_url=''                            where name='BdRDungeon';
SQL

2. Check the read path carries the cleaned values.

"Should show source: supabase and the normalised values"
curl -s localhost:8420/api/ecosystem | python3 -m json.tool | grep -E 'source|runs_on|database|status'

3. Apply Part C — rebuild the view, drop the old tables, add RLS/grants.
   Run only after step 2 looks right.

"Rebuild fleet_ecosystem_json without the derived apps key / agents line, then drop + lock down"
cd ~/projects/BdRDev
# a) edit the create-or-replace for public.fleet_ecosystem_json (it's the
#    Part B block in supabase/DRAFT_fold_apps_into_projects.sql): delete
#    the whole 'apps' jsonb object and the 'agents' line from the
#    projects object, then run that create-or-replace against supabase-db.
# b) then:
docker exec -i supabase-db psql -U postgres -v ON_ERROR_STOP=1 <<'SQL'
drop table if exists public.apps;
drop table if exists public.project_agents;
alter table public.roles         enable row level security;
alter table public.project_roles enable row level security;
create policy roles_read_all         on public.roles         for select to anon, authenticated using (true);
create policy roles_service_all      on public.roles         for all    to service_role using (true) with check (true);
create policy project_roles_read_all on public.project_roles for select to anon, authenticated using (true);
create policy project_roles_service_all on public.project_roles for all to service_role using (true) with check (true);
grant select on public.roles, public.project_roles to anon, authenticated;
grant select, insert, update, delete on public.roles, public.project_roles to service_role;
grant usage, select on all sequences in schema public to service_role;
SQL

4. Reload the Ecosystem tab — both grids should still load and
   round-trip. Then archive this file with a one-line note on how it went.

@@@ --------------- @@@

Notes:
- `supabase/DRAFT_fold_apps_into_projects.sql` Part C holds the same
  block (commented) plus the view-rebuild note.
- The `app/common.py` read shim for the old `apps` shape was already
  removed on the 2026-09-03 pass, so nothing app-side depends on the old
  tables or view keys.
