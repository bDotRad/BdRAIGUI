-- Part B + Part C only, extracted from supabase/DRAFT_fold_apps_into_projects.sql
-- (running the full file would re-run Part A's data migration and clobber the
--  already-applied step-1 row normalisation.)

begin;

-- ===== PART B - swap the view (already in post-C form) =====
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

-- ===== PART C - contract =====
drop table if exists public.apps;
drop table if exists public.project_agents;

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

commit;
