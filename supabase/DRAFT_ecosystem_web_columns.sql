-- ============================================================================
-- DRAFT MIGRATION  -  servers: split web access into local_url + ts_url,
--                     drop software_freetext
-- ----------------------------------------------------------------------------
-- STATUS: DRAFT. Deliberately NOT placed in migrations/ so it does not get
-- picked up by an unattended schema-apply. Run by hand on the self-hosted
-- Supabase (supabase-db container) on the dev box, same as
-- DRAFT_fold_apps_PartBC_only.sql was.
--
-- Tracked by:  _Requests/rEcosystem web-access columns/request.md
-- Design:      supabase/DATA_MODEL.md  ("server" field table)
--
-- COUPLED to app code. The matching app/common.py + app/fleet_db.py +
-- app/templates/index.html change (local_url / ts_url, no software) must be
-- deployed together with this: run this file, THEN restart the dashboard.
-- In between, the running (old) dashboard keeps working off state/ecosystem.json
-- if its Supabase read trips on the shape change.
--
-- Target: Postgres 17, self-hosted Supabase. Safe to re-run (guarded rename,
-- add/drop if exists, name-keyed data updates that no-op on a second pass).
--
-- Run order matters: recreate the view (dropping its dependency on
-- software_freetext) BEFORE dropping that column.
-- ============================================================================

begin;

-- ===========================================================================
-- 1.  SCHEMA  -  rename web_url -> local_url, add ts_url
-- ===========================================================================
do $$
begin
  if exists (
    select 1 from information_schema.columns
    where table_schema = 'public' and table_name = 'servers'
      and column_name = 'web_url'
  ) then
    alter table public.servers rename column web_url to local_url;
  end if;
end $$;

alter table public.servers add column if not exists ts_url text not null default '';

comment on column public.servers.local_url is
  'LAN / mDNS address (e.g. https://<host>.local). Rendered as a link. Was web_url.';
comment on column public.servers.ts_url is
  'Primary Tailscale front-door URL (https://<node>.tail0ed3f6.ts.net[:port]). '
  'Blank where the box is not on the tailnet or `tailscale serve` is not set up. '
  'Per-app tailnet ports are not modelled here.';


-- ===========================================================================
-- 2.  VIEW  -  fleet_ecosystem_json, server object now carries local_url +
--             ts_url instead of web_url + software. Must run before the
--             software_freetext drop below (releases the view's dependency).
-- ===========================================================================
create or replace view public.fleet_ecosystem_json
with (security_invoker = true) as
select jsonb_build_object(
  'servers', (
    select coalesce(jsonb_agg(t.obj order by t.sort_order, t.name), '[]'::jsonb)
    from (
      select sv.sort_order, sv.name,
        jsonb_build_object(
          'name', sv.name, 'tag', sv.tag, 'address', sv.address,
          'tailscale', sv.tailscale_ip,
          'local_url', sv.local_url,
          'ts_url', sv.ts_url,
          'host', sv.host, 'os', sv.os, 'ram', sv.ram, 'disk', sv.disk,
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

comment on view public.fleet_ecosystem_json is
  'Single-row view. Column "ecosystem" (jsonb) matches common.load_ecosystem(): '
  'servers[]={name,tag,address,tailscale,local_url,ts_url,host,os,ram,disk,'
  'claude,nginx,supabase,sqlite,git,provisioned,dev_host}; '
  'projects[]={name,exists,runs_on,web_url,database,status,roles[]}; notes"".';

grant select on public.fleet_ecosystem_json to anon, authenticated, service_role;


-- ===========================================================================
-- 3.  SCHEMA  -  drop the now-unreferenced software_freetext column
-- ===========================================================================
alter table public.servers drop column if exists software_freetext;


-- ===========================================================================
-- 4.  DATA LOAD  -  ecosystem-servers-tidied.csv from the request folder
-- ===========================================================================
-- Renames key off the OLD name, so a second run is a no-op for those rows.

-- BdRVSrvDev -> BdRPiSrvDev  (now a Pi at 10.10.8.11; Supabase runs here too)
update public.servers set
  name         = 'BdRPiSrvDev',
  tag          = 'this host, local',
  address      = '10.10.8.11',
  tailscale_ip = '100.116.147.74',
  local_url    = 'https://bdrpisrvdev.local',
  ts_url       = 'https://bdrpisrvdev.tail0ed3f6.ts.net',
  host         = 'Raspberry Pi',
  os           = 'Ubuntu Server',
  ram          = '8GB',
  disk         = '512GB SSD',
  provisioned  = true,
  dev_host     = true
where name = 'BdRVSrvDev';

-- Supabase now runs on the dev box (127.0.0.1:8000) -> add the software link
insert into public.server_software (server_id, software_id)
select s.id, sw.id
from public.servers s
cross join public.software sw
where s.name = 'BdRPiSrvDev' and sw.name = 'Supabase'
on conflict do nothing;

-- BdRPiAMI -> BdRPiSrvAMI  (matches Tailscale node bdrpisrvami + the nginx configs)
update public.servers set
  name         = 'BdRPiSrvAMI',
  tag          = 'Raspberry Pi 8GB',
  address      = '10.10.10.20',
  tailscale_ip = '100.86.25.88',
  local_url    = 'https://bdrpiami.local',
  ts_url       = '',                       -- tailscale serve not set up there yet
  host         = 'Raspberry Pi',
  os           = 'Raspberry Pi',
  ram          = '8GB',
  provisioned  = true,
  dev_host     = false
where name = 'BdRPiAMI';

-- BdRSrvDungeon  -  not provisioned, both URLs blank
update public.servers set
  local_url   = '',
  ts_url      = '',
  provisioned = false
where name = 'BdRSrvDungeon';

-- BdRBirdDetector  -  LAN only, plain http (no TLS on that box), not on tailnet
update public.servers set
  local_url = 'http://bdrbirddetector.local',
  ts_url    = ''
where name = 'BdRBirdDetector';

-- Refresh PostgREST's schema cache so the renamed column shows on the REST API.
notify pgrst, 'reload schema';

commit;


-- ===========================================================================
-- SANITY CHECKS  (run after COMMIT)
-- ===========================================================================
-- select name, address, local_url, ts_url, provisioned, dev_host
--   from public.servers order by sort_order, name;
-- select jsonb_pretty((select ecosystem->'servers' from public.fleet_ecosystem_json));
-- \d public.servers   -- expect local_url + ts_url, no software_freetext
