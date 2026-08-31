WAITING RESPONSE

## Where this is up to (scheduled pass, 2026-08-31 ~16:30)

You'd already carried this further than the file said. Current reality:

**Done:**

- ✅ Local Supabase on BdRVSrvDev up (11 containers healthy), dashboard
  reads from it — `curl localhost:8420/api/ecosystem` → `"source":"supabase"`.
- ✅ **Migration Part A** (add columns + `roles` / `project_roles`
  tables, migrate `apps` / `project_agents` across) — applied.
- ✅ **Migration Part B** (swap `fleet_ecosystem_json` to the new shape)
  — applied. The view now emits `projects[].runs_on / web_url / database
  / status / roles`.
- ✅ **Dashboard restarted** (live process started 2026-08-31 13:36) and
  is serving the new template + reading the new view. Report query 1
  ("agents mapped to no role") comes back **clean — 0 rows**.
- ✅ **App code committed + pushed** (`148259d`): one Ecosystem tab, the
  Servers + Projects grids, Edit button top-right, no notes blob on the
  page. `apps` / `projects[].agents` gone from the write path;
  `_Instructions/WebUI.md` reference impl refreshed.

**Still needs you (2 things):**

1. **Data cleanup + write-path check.** Report query 2 flags 5 projects
   whose `database` / `web_url` are still the old free-text `apps`
   values, and every project came across as `status = deployed`. The
   cleanest fix also verifies the write path: open the **Ecosystem** tab
   → **Edit** → fix the Projects grid → **Save** (status should read
   "Saved to Supabase"), reload, confirm it stuck. Suggested values:

   | Project | runs_on | Web URL | Database | Status |
   |---|---|---|---|---|
   | BdRDev | BdRVSrvDev | http://192.168.100.10:8420 | none | live |
   | BdRAMAssist | BdRPiAMI | *(blank)* | shares:PlanBdRad | building |
   | PlanBdRad | BdRPiAMI | https://planbdrad.local | Supabase | building |
   | BdRIS | *(blank)* | *(blank)* | none | planned |
   | BdRBirdDetector | BdRBirdDetector | *(blank)* | none | building |
   | BdRDungeon | BdRSrvDungeon | *(blank)* | Supabase | planned |

   (Server names in the DB are still `BdRPiAMI` / `BdRVSrvDev` etc. — the
   `BdRPiSrvAMI` rename is display-only in this data and not part of this
   request. Fix it in the Servers grid too if you want, or leave it.)

   If you'd rather do it in SQL, the equivalent is in the Action block.

2. **Part C** (drop `apps` / `project_agents`, add RLS + grants for
   `roles` / `project_roles`, rebuild the view without the derived
   `apps` key + `agents` line). Destructive — run only after step 1
   confirms the new UI round-trips. Action block below.

An unattended pass won't drop tables on the source-of-truth DB or run
the write-path test in a browser, and the step-1 values are your call —
hence WAITING RESPONSE. After you've done both, flip this to `READY`
(with a note) and the next scheduled pass removes the transitional read
shim from `app/common.py` and archives this.

??? --- Question --- ???

Anything in the "Brad's final spec" Projects grid you want changed now
that it's built?

Options:
1. Ship it as spec'd — Name, 6 role Y/N cols, Runs on, Web URL,
   Database, Status. The `exists` flag is still stored, just not shown.
2. Bring the `exists` flag back as a visible Y/N column.
3. Other change (write it in).

Answer: proceeding on **1** (you flipped to READY without changing the
spec; the "should be ecosystem 2 only" note matches it). Say so here and
re-open if you want 2 or 3.

??? --------------- ???

@@@ --- Action (Brad) --- @@@

All on this dev box (BdRVSrvDev). `docker exec -i supabase-db psql -U
postgres` is the SQL shell — no sudo for the DB parts.

1. (Optional — only if you skip the Ecosystem-tab Edit/Save in step 1
   above and want to do the data cleanup in SQL instead.)

"Normalise the 5 flagged projects to the enum + real URLs"
docker exec -i supabase-db psql -U postgres -v ON_ERROR_STOP=1 <<'SQL'
update public.projects set database='none',              status='live',     web_url='http://192.168.100.10:8420' where name='BdRDev';
update public.projects set database='shares:PlanBdRad',  status='building', web_url=''                            where name='BdRAMAssist';
update public.projects set database='Supabase',          status='building', web_url='https://planbdrad.local'     where name='PlanBdRad';
update public.projects set database='none',              status='planned',  web_url=''                            where name='BdRIS';
update public.projects set database='none',              status='building', web_url=''                            where name='BdRBirdDetector';
update public.projects set database='Supabase',          status='planned',  web_url=''                            where name='BdRDungeon';
SQL

2. Verify the read path carries the cleaned fields.

"Should show source: supabase and the normalised values"
curl -s localhost:8420/api/ecosystem | python3 -m json.tool | grep -E 'source|runs_on|database|status'

   Then in the browser: Ecosystem tab → Edit → toggle a role / change a
   cell on each grid → Save ("Saved to Supabase") → reload, confirm it
   stuck. Confirm there's no Ecosystem 2 / Fleet tab and no blurb
   above/below either grid.

3. Apply Part C (contract). Run only after step 2 is good.

"Run Part C — rebuild the view without the derived apps key, drop the old tables, add RLS/grants"
cd ~/projects/BdRDev
# a) rebuild fleet_ecosystem_json: same as Part B but delete the whole
#    'apps' jsonb object and the 'agents' line from the projects object,
#    then run that create-or-replace.
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

   (`supabase/DRAFT_fold_apps_into_projects.sql` Part C has the same
   block, commented, plus the view-rebuild note.)

4. Reload the Ecosystem tab once more — both grids should still load and
   round-trip. Then set this file's first line to `READY` with a one-line
   note on how it went.

@@@ --------------- @@@

---
---

## Earlier history (kept for the record)

Both questions at the very bottom were answered 2026-08-29: **delete the
old Ecosystem tab**, **drop the notes blob from the page** (stays in DB).

### Note Brad left on the 2026-08-31 pass (verbatim)

> docker exec -i supabase-db psql -U postgres -c "select name, status,
> database, web_url from public.projects where database !~
> '^(|none|SQLite|Supabase|shares:.*)\$' or web_url ilike '%not
> deployed%' or web_url ilike '%no fixed url%' or web_url ilike '%local
> network%';"
>
> [pasted terminal output — the psql call got mangled by a shell paste
> (`~/projects/update.sh` spliced into the middle) and errored with
> `schema "update" does not exist`. That's the shell, not the DB — the
> query itself is report query 2 above and it ran fine on this pass.]
>
> Supabase is now setup. I dont know where the ecosystem thing is up to.
> should be ecosystem 2 only but changed to ecosystem. all in supabase

### Brad's final spec (2026-08-30)

a. Remove the **Ecosystem** tab.
b. Remove the **Fleet** tab.
c. Rename **Ecosystem 2** → **Ecosystem**.
d. Remove the text above *and* below the table.
e. Edit button → top right of the table.
f. Add a **Projects** table below the **Servers** table:

| Col | Type |
|---|---|
| Name | text |
| PM | Y/N |
| Web | Y/N |
| DB | Y/N |
| Elec Ctrl | Y/N |
| Elec LV-HV | Y/N |
| Doco | Y/N |
| Runs on | dropdown of servers (blank = not deployed) |
| Web URL | text, rendered as a link in read mode |
| Database | `none` / `SQLite` / `Supabase` / `shares:<project>` |
| Status | `planned` / `building` / `deployed` / `live` |

Supersedes **`rFlet update`** and **`rUpdate Fleet - Add Project
Table`** (folded in verbatim below). Does **not** cover `rFix all of the
web pages` — separate concern, left in place.

- Design + rationale: `supabase/DATA_MODEL.md`
- Draft schema change: `supabase/DRAFT_fold_apps_into_projects.sql`

### Original open questions (both answered)

> The old **Ecosystem** tab is an ASCII tree + fleet diagram. Keep it
> once the two grids exist?
> Answer: 1 — delete it.

> The fleet **notes** blob (`fleet_meta.notes`). Keep it on the page?
> Answer: 1 — drop it from the page (stays in the DB).

===========================================================================
SUPERSEDED REQUESTS (verbatim)
===========================================================================

----- _Requests/rFlet update.md -----

READY

Get rid of the notes and the blurb at the top. i jsut want the table. move the edit button to the top right

----- _Requests/rUpdate Fleet - Add Project Table.md -----

READY

IMPORTANT.... I MEANT ECOSYSTEM 2 Page not FLEET.

I am looking to get rid of FLEET and ECOSYSTEM

Projects
     |              Dev Agents                  | Software    |
Name | PM, Web, DB, Elec Ctrl, Elec LV HV, Doco |  Web  | DB  |

Name - Text
Dev Agents - Y,N
Software - Web is the Web Address or blank. DB = SQL Lite or Supabase

(The file also carried a pasted console snapshot from 2026-08-29 15:35 —
unrelated terminal output from the rFix-all-web-pages pass, not part of
the ask; dropped here.)
