-- ============================================================================
-- DRAFT MIGRATION  -  fold `apps` into `projects`
-- ----------------------------------------------------------------------------
-- STATUS: DRAFT. Deliberately NOT placed in migrations/ so it does not get
-- picked up by an unattended schema-apply or a sql_output.sql regen.
--
-- Design + rationale: supabase/DATA_MODEL.md
-- Tracked by:         _Requests/rEcosystemConsolidation.md
--
-- This change is COUPLED to app code. Running Part B (the view swap) before
-- app/fleet_db.py + app/common.py understand the new shape will break the
-- dashboard's write path (it will silently fall back to state/ecosystem.json).
-- Run order:
--   Part A  - expand: add columns + role tables, migrate data.  Safe anytime.
--   Part B  - swap the fleet_ecosystem_json view to the new shape.
--             Run together with the app-code change + dashboard restart.
--   Part C  - contract: drop `apps` and `project_agents`.
--             Run only after the new UI is verified working.
--
-- Target: Postgres 17, self-hosted Supabase on BdRPiSrvAMI.
-- Safe to re-run (create ... if not exists / update ... where).
-- ============================================================================


-- ===========================================================================
-- PART A  -  EXPAND
-- ===========================================================================

-- --- projects: absorb the deployment facet -------------------------------
alter table public.projects add column if not exists runs_on_server_id bigint
  references public.servers(id) on delete set null;
alter table public.projects add column if not exists web_url  text not null default '';
alter table public.projects add column if not exists database text not null default '';
alter table public.projects add column if not exists status   text not null default 'planned';

alter table public.projects drop constraint if exists projects_status_chk;
alter table public.projects add  constraint projects_status_chk
  check (status in ('planned', 'building', 'deployed', 'live'));

comment on column public.projects.runs_on_server_id is
  'The server this project''s app is deployed on. NULL = not deployed. Was apps.server_id.';
comment on column public.projects.database is
  'none | SQLite | Supabase | shares:<project>. Was apps.db (free text - needs a cleanup pass).';

create index if not exists projects_runs_on_idx on public.projects (runs_on_server_id);


-- --- roles: dev-agent role matrix, modelled like software ----------------
create table if not exists public.roles (
  id         bigint generated always as identity primary key,
  name       text        not null unique,   -- stable key
  label      text        not null default '', -- column header shown in the UI
  sort_order integer     not null default 0,
  created_at timestamptz not null default now()
);

comment on table public.roles is
  'Catalogue of dev-agent roles a project can have. project_roles is the M:N link. Replaces the free-text project_agents table.';

insert into public.roles (name, label, sort_order) values
  ('pm',       'PM',          1),
  ('web',      'Web',         2),
  ('db',       'DB',          3),
  ('elec_ctrl','Elec Ctrl',   4),
  ('elec_lvhv','Elec LV-HV',  5),
  ('doco',     'Doco',        6)
on conflict (name) do update set label = excluded.label, sort_order = excluded.sort_order;

create table if not exists public.project_roles (
  project_id bigint not null references public.projects(id) on delete cascade,
  role_id    bigint not null references public.roles(id)    on delete cascade,
  primary key (project_id, role_id)
);

create index if not exists project_roles_role_id_idx on public.project_roles (role_id);


-- --- data migration: apps -> projects -----------------------------------
-- Match each app to a project by exact name, then by prefix
-- ("BdRDev dashboard + scheduler" -> "BdRDev").
with matched as (
  select
    ap.id  as app_id,
    pr.id  as project_id,
    ap.server_id,
    ap.server_name,
    ap.web_address,
    ap.db,
    ap.planned
  from public.apps ap
  join public.projects pr
    on pr.name = ap.name
    or ap.name ilike pr.name || ' %'
)
update public.projects p set
  runs_on_server_id = coalesce(
    m.server_id,
    (select s.id from public.servers s where s.name = m.server_name)
  ),
  web_url  = m.web_address,
  database = m.db,
  status   = case when m.planned then 'planned' else 'deployed' end
from matched m
where p.id = m.project_id;

-- project_agents -> project_roles  (best-effort name mapping; anything that
-- matches nothing is left for a manual pass - see the report query at the end).
insert into public.project_roles (project_id, role_id)
select distinct pa.project_id, r.id
from public.project_agents pa
join public.roles r on r.name = case
  when pa.agent_name ilike '%project manager%' or pa.agent_name ilike 'pm'        then 'pm'
  when pa.agent_name ilike '%web%'                                                then 'web'
  when pa.agent_name ilike '%sql%' or pa.agent_name ilike '%supabase%'
       or pa.agent_name ilike '%database%'                                        then 'db'
  when pa.agent_name ilike '%esp32%' or pa.agent_name ilike '%electronic%'        then 'elec_ctrl'
  when pa.agent_name ilike '%doc%'                                                then 'doco'
  else null
end
on conflict do nothing;


-- ===========================================================================
-- PART B  -  SWAP THE VIEW   (run with the app-code change + restart)
-- ===========================================================================
-- New `projects` shape: adds runs_on / web_url / database / status / roles.
--
-- 2026-09-04: this create-or-replace has been updated to its Part C form -
-- the transitional top-level `apps` key and `projects[].agents` line are
-- gone. Re-run this block as part of Part C, then run the drops/RLS below.

create or replace view public.fleet_ecosystem_json
with (security_invoker = true) as
select jsonb_build_object(
  'servers', (
    select coalesce(jsonb_agg(t.obj order by t.sort_order, t.name), '[]'::jsonb)
    from (
      select sv.sort_order, sv.name,
        jsonb_build_object(
          'name', sv.name, 'tag', sv.tag, 'address', sv.address,
          'tailscale', sv.tailscale_ip, 'web_url', sv.web_url,
          'host', sv.host, 'os', sv.os, 'ram', sv.ram, 'disk', sv.disk,
          'software', sv.software_freetext,
          'claude',   exists (select 1 from public.server_software ss join public.software sw on sw.id = ss.software_id where ss.server_id = sv.id and sw.name = 'Claude Code'),
          'nginx',    exists (select 1 from public.server_software ss join public.software sw on sw.id = ss.software_id where ss.server_id = sv.id and sw.name = 'Nginx'),
          'supabase', exists (select 1 from public.server_software ss join public.software sw on sw.id = ss.software_id where ss.server_id = sv.id and sw.name = 'Supabase'),
          'sqlite',   exists (select 1 from public.server_software ss join public.software sw on sw.id = ss.software_id where ss.server_id = sv.id and sw.name = 'SQLite'),
          'git', sv.git_notes, 'provisioned', sv.provisioned, 'dev_host', sv.dev_host
        ) as obj
      from public.servers sv
    ) t
  ),
  'projects', (
    select coalesce(jsonb_agg(t.obj order by t.sort_order, t.name), '[]'::jsonb)
    from (
      select pr.sort_order, pr.name,
        jsonb_build_object(
          'name',     pr.name,
          'exists',   pr.exists_flag,
          'runs_on',  coalesce((select s.name from public.servers s where s.id = pr.runs_on_server_id), ''),
          'web_url',  pr.web_url,
          'database', pr.database,
          'status',   pr.status,
          'roles',    coalesce((
            select jsonb_agg(r.name order by r.sort_order)
            from public.project_roles prr join public.roles r on r.id = prr.role_id
            where prr.project_id = pr.id
          ), '[]'::jsonb)
        ) as obj
      from public.projects pr
    ) t
  ),
  'notes', coalesce((select notes from public.fleet_meta where id = 1), '')
) as ecosystem;

grant select on public.fleet_ecosystem_json to anon, authenticated, service_role;


-- ===========================================================================
-- PART C  -  CONTRACT   (only after the new UI is verified working)
-- ===========================================================================
-- Run once app/fleet_db.py no longer writes `apps` and the dashboard no
-- longer reads the top-level `apps` key or `projects[].agents` (both true
-- as of the 2026-09-03 app pass). Re-run the Part B create-or-replace above
-- FIRST (it is now in its post-C form), then run this block.

drop table if exists public.apps;
drop table if exists public.project_agents;

-- RLS + grants for the new tables (mirror the base schema's do-block)
alter table public.roles         enable row level security;
alter table public.project_roles enable row level security;
drop policy if exists roles_read_all            on public.roles;
drop policy if exists roles_service_all         on public.roles;
drop policy if exists project_roles_read_all    on public.project_roles;
drop policy if exists project_roles_service_all on public.project_roles;
create policy roles_read_all         on public.roles         for select to anon, authenticated using (true);
create policy roles_service_all      on public.roles         for all    to service_role using (true) with check (true);
create policy project_roles_read_all on public.project_roles for select to anon, authenticated using (true);
create policy project_roles_service_all on public.project_roles for all to service_role using (true) with check (true);
grant select on public.roles, public.project_roles to anon, authenticated;
grant select, insert, update, delete on public.roles, public.project_roles to service_role;
grant usage, select on all sequences in schema public to service_role;


-- ===========================================================================
-- POST-MIGRATION REPORT  -  run after Part A, clean up by hand
-- ===========================================================================
-- Agents that mapped to no role:
--   select p.name, pa.agent_name
--   from public.project_agents pa join public.projects p on p.id = pa.project_id
--   where not exists (
--     select 1 from public.project_roles prr where prr.project_id = pa.project_id
--   );
--
-- Deployment free-text that needs normalising to the enum / a real URL:
--   select name, status, database, web_url from public.projects
--   where database !~ '^(|none|SQLite|Supabase)$' or web_url ilike '%not deployed%'
--      or web_url ilike '%no fixed url%' or web_url ilike '%local network%';
