-- ============================================================================
-- BdRDev fleet / ecosystem schema
-- ----------------------------------------------------------------------------
-- Moves the fleet data that currently lives in state/ecosystem.json (seeded
-- from common.DEFAULT_ECOSYSTEM) into a normalised Postgres model on the
-- self-hosted Supabase instance (BdRPiAMI).
--
-- Model:
--   servers            - one row per fleet machine
--   software           - canonical software / service catalogue
--   server_software    - M:N: which software runs on which server
--   projects           - one row per Claude Code project
--   project_agents     - child of projects: the agent names for a project
--   apps               - deployed / planned apps and where they run
--   fleet_meta         - single-row table holding the free-text notes blob
--
-- The dashboard reads everything back through ONE view,
-- public.fleet_ecosystem_json, whose single jsonb column `ecosystem` is
-- shaped exactly like common.load_ecosystem()'s return value.
--
-- This file is written to be safe to re-run (create ... if not exists /
-- or replace, drop-then-create for policies and triggers).
--
-- Target: Postgres 17, self-hosted Supabase. Roles assumed to exist:
--   anon, authenticated, service_role.
-- ============================================================================

-- ---------------------------------------------------------------------------
-- shared: updated_at maintenance
-- ---------------------------------------------------------------------------
create or replace function public.set_updated_at()
returns trigger
language plpgsql
as $$
begin
  new.updated_at := now();
  return new;
end;
$$;

-- ---------------------------------------------------------------------------
-- servers
-- ---------------------------------------------------------------------------
create table if not exists public.servers (
  id                bigint generated always as identity primary key,
  name              text        not null unique,
  tag               text        not null default '',   -- short parenthetical shown next to the name
  address           text        not null default '',   -- primary IP / hostname
  tailscale_ip      text        not null default '',   -- Tailscale tailnet IP, e.g. 100.x.y.z
  web_url           text        not null default '',   -- primary web UI URL (rendered as a link)
  host              text        not null default '',    -- "VM" | "Raspberry Pi" | "Physical"
  os                text        not null default '',
  ram               text        not null default '',
  disk              text        not null default '',
  software_freetext text        not null default '',    -- diagram wording + "Other" column; e.g. "Claude Code . Nginx . Supabase"
  git_notes         text        not null default '',    -- multi-line GitHub/Firebase push/pull notes
  provisioned       boolean     not null default true,
  dev_host          boolean     not null default false, -- the single dev box / source of truth
  sort_order        integer     not null default 0,
  created_at        timestamptz not null default now(),
  updated_at        timestamptz not null default now()
);

comment on table  public.servers is 'One row per fleet machine (dev box, Pis, VMs).';
comment on column public.servers.software_freetext is 'Free-text software list for the diagram / "Other" column. The tracked per-package booleans in fleet_ecosystem_json are derived from server_software, not from this string.';
comment on column public.servers.dev_host is 'True for the one machine that is the dev box / single source of truth. At most one row may be true.';

-- Columns added after first release; ALTER for installs created before them
-- (the create-table above already has them for fresh installs). Idempotent.
alter table public.servers add column if not exists tailscale_ip text not null default '';
alter table public.servers add column if not exists web_url      text not null default '';

-- at most one dev host
create unique index if not exists servers_single_dev_host_idx
  on public.servers (dev_host) where dev_host;
create index if not exists servers_sort_order_idx on public.servers (sort_order);

drop trigger if exists servers_set_updated_at on public.servers;
create trigger servers_set_updated_at
  before update on public.servers
  for each row execute function public.set_updated_at();

-- ---------------------------------------------------------------------------
-- software (catalogue)
-- ---------------------------------------------------------------------------
create table if not exists public.software (
  id          bigint generated always as identity primary key,
  name        text        not null unique,
  description text        not null default '',
  created_at  timestamptz not null default now(),
  updated_at  timestamptz not null default now()
);

comment on table public.software is 'Canonical catalogue of software / services that can run on a server. "SQL Lite" from the old JSON is normalised to "SQLite" here.';

drop trigger if exists software_set_updated_at on public.software;
create trigger software_set_updated_at
  before update on public.software
  for each row execute function public.set_updated_at();

-- ---------------------------------------------------------------------------
-- server_software (M:N)
-- ---------------------------------------------------------------------------
create table if not exists public.server_software (
  server_id   bigint not null references public.servers(id)  on delete cascade,
  software_id bigint not null references public.software(id) on delete cascade,
  primary key (server_id, software_id)
);

comment on table public.server_software is 'Which software runs on which server. The claude/nginx/supabase/sqlite booleans in fleet_ecosystem_json are EXISTS checks against this table joined to software.name.';

-- PK already indexes (server_id, software_id); add the reverse for FK lookups
create index if not exists server_software_software_id_idx
  on public.server_software (software_id);

-- ---------------------------------------------------------------------------
-- projects
-- ---------------------------------------------------------------------------
create table if not exists public.projects (
  id          bigint generated always as identity primary key,
  name        text        not null unique,
  exists_flag boolean     not null default true,  -- exposed as "exists" in fleet_ecosystem_json
  sort_order  integer     not null default 0,
  created_at  timestamptz not null default now(),
  updated_at  timestamptz not null default now()
);

comment on table  public.projects is 'One row per Claude Code project under ~/projects.';
comment on column public.projects.exists_flag is 'Whether the project actually exists on disk yet. Rendered as the JSON key "exists" (which is a reserved word, hence the _flag suffix here).';

create index if not exists projects_sort_order_idx on public.projects (sort_order);

drop trigger if exists projects_set_updated_at on public.projects;
create trigger projects_set_updated_at
  before update on public.projects
  for each row execute function public.set_updated_at();

-- ---------------------------------------------------------------------------
-- project_agents (child of projects)
-- ---------------------------------------------------------------------------
create table if not exists public.project_agents (
  id         bigint generated always as identity primary key,
  project_id bigint  not null references public.projects(id) on delete cascade,
  agent_name text    not null,
  sort_order integer not null default 0,
  unique (project_id, agent_name)
);

comment on table public.project_agents is 'The named .claude/agents entries for a project. Agents are just names here.';

create index if not exists project_agents_project_id_idx
  on public.project_agents (project_id);

-- ---------------------------------------------------------------------------
-- apps
-- ---------------------------------------------------------------------------
create table if not exists public.apps (
  id          bigint generated always as identity primary key,
  name        text        not null unique,
  server_id   bigint      references public.servers(id) on delete set null, -- nullable: raw name may not match a row
  server_name text        not null default '',   -- raw server name from the source data, kept verbatim
  tag         text        not null default '',
  web_address text        not null default '',
  db          text        not null default '',
  planned     boolean     not null default false,
  sort_order  integer     not null default 0,
  created_at  timestamptz not null default now(),
  updated_at  timestamptz not null default now()
);

comment on table  public.apps is 'Deployed or planned apps and which server they run on.';
comment on column public.apps.server_name is 'Raw server name as given in the source data. server_id is the resolved FK where the name matches a servers row, else NULL.';

create index if not exists apps_server_id_idx  on public.apps (server_id);
create index if not exists apps_sort_order_idx on public.apps (sort_order);

drop trigger if exists apps_set_updated_at on public.apps;
create trigger apps_set_updated_at
  before update on public.apps
  for each row execute function public.set_updated_at();

-- ---------------------------------------------------------------------------
-- fleet_meta (single row)
-- ---------------------------------------------------------------------------
create table if not exists public.fleet_meta (
  id         integer     primary key default 1,
  notes      text        not null default '',
  updated_at timestamptz not null default now(),
  constraint fleet_meta_singleton check (id = 1)
);

comment on table public.fleet_meta is 'Single-row table (id is forced to 1) holding the free-text fleet notes blob.';

drop trigger if exists fleet_meta_set_updated_at on public.fleet_meta;
create trigger fleet_meta_set_updated_at
  before update on public.fleet_meta
  for each row execute function public.set_updated_at();

-- ---------------------------------------------------------------------------
-- Row Level Security
--   service_role: full access (also has BYPASSRLS, policy is belt-and-braces)
--   anon / authenticated: SELECT only
-- The dashboard talks to Supabase server-side with the service key; anon-read
-- is kept open so the data stays easy to consume from elsewhere.
-- ---------------------------------------------------------------------------
do $$
declare
  t text;
begin
  foreach t in array array[
    'servers', 'software', 'server_software',
    'projects', 'project_agents', 'apps', 'fleet_meta'
  ]
  loop
    execute format('alter table public.%I enable row level security;', t);

    execute format('drop policy if exists %I on public.%I;', t || '_service_role_all', t);
    execute format(
      'create policy %I on public.%I for all to service_role using (true) with check (true);',
      t || '_service_role_all', t);

    execute format('drop policy if exists %I on public.%I;', t || '_read_all', t);
    execute format(
      'create policy %I on public.%I for select to anon, authenticated using (true);',
      t || '_read_all', t);
  end loop;
end;
$$;

-- ---------------------------------------------------------------------------
-- Grants (PostgREST roles need table/sequence privileges independent of RLS)
-- ---------------------------------------------------------------------------
grant usage on schema public to anon, authenticated, service_role;

grant select on
  public.servers, public.software, public.server_software,
  public.projects, public.project_agents, public.apps, public.fleet_meta
  to anon, authenticated;

grant select, insert, update, delete on
  public.servers, public.software, public.server_software,
  public.projects, public.project_agents, public.apps, public.fleet_meta
  to service_role;

grant usage, select on all sequences in schema public to service_role;

-- ---------------------------------------------------------------------------
-- fleet_ecosystem_json
--   ONE row, ONE column `ecosystem` (jsonb), shaped exactly like
--   common.load_ecosystem()'s output. This is the contract the dashboard
--   reads. security_invoker so the caller's own SELECT privileges / RLS
--   apply (anon-read is allowed, service key sees everything).
-- ---------------------------------------------------------------------------
create or replace view public.fleet_ecosystem_json
with (security_invoker = true) as
select jsonb_build_object(
  'servers', (
    select coalesce(jsonb_agg(t.obj order by t.sort_order, t.name), '[]'::jsonb)
    from (
      select
        sv.sort_order,
        sv.name,
        jsonb_build_object(
          'name',        sv.name,
          'tag',         sv.tag,
          'address',     sv.address,
          'tailscale',   sv.tailscale_ip,
          'web_url',      sv.web_url,
          'host',        sv.host,
          'os',          sv.os,
          'ram',         sv.ram,
          'disk',        sv.disk,
          'software',    sv.software_freetext,
          'claude',   exists (select 1 from public.server_software ss join public.software sw on sw.id = ss.software_id
                               where ss.server_id = sv.id and sw.name = 'Claude Code'),
          'nginx',    exists (select 1 from public.server_software ss join public.software sw on sw.id = ss.software_id
                               where ss.server_id = sv.id and sw.name = 'Nginx'),
          'supabase', exists (select 1 from public.server_software ss join public.software sw on sw.id = ss.software_id
                               where ss.server_id = sv.id and sw.name = 'Supabase'),
          'sqlite',   exists (select 1 from public.server_software ss join public.software sw on sw.id = ss.software_id
                               where ss.server_id = sv.id and sw.name = 'SQLite'),
          'git',         sv.git_notes,
          'provisioned', sv.provisioned,
          'dev_host',    sv.dev_host
        ) as obj
      from public.servers sv
    ) t
  ),
  'projects', (
    select coalesce(jsonb_agg(t.obj order by t.sort_order, t.name), '[]'::jsonb)
    from (
      select
        pr.sort_order,
        pr.name,
        jsonb_build_object(
          'name',   pr.name,
          'exists', pr.exists_flag,
          'agents', coalesce((
            select jsonb_agg(pa.agent_name order by pa.sort_order, pa.id)
            from public.project_agents pa
            where pa.project_id = pr.id
          ), '[]'::jsonb)
        ) as obj
      from public.projects pr
    ) t
  ),
  'apps', (
    select coalesce(jsonb_agg(t.obj order by t.sort_order, t.name), '[]'::jsonb)
    from (
      select
        ap.sort_order,
        ap.name,
        jsonb_build_object(
          'name',        ap.name,
          'server',      coalesce(nullif(ap.server_name, ''),
                                  (select name from public.servers where id = ap.server_id),
                                  ''),
          'tag',         ap.tag,
          'web_address', ap.web_address,
          'db',          ap.db,
          'planned',     ap.planned
        ) as obj
      from public.apps ap
    ) t
  ),
  'notes', coalesce((select notes from public.fleet_meta where id = 1), '')
) as ecosystem;

comment on view public.fleet_ecosystem_json is
  'Single-row view. Column "ecosystem" (jsonb) matches common.load_ecosystem(): {servers:[{name,tag,address,tailscale,web_url,host,os,ram,disk,software,claude,nginx,supabase,sqlite,git,provisioned,dev_host}], projects:[{name,exists,agents:[]}], apps:[{name,server,tag,web_address,db,planned}], notes:""}. The dashboard reads this; state/ecosystem.json stays as a fallback cache.';

grant select on public.fleet_ecosystem_json to anon, authenticated, service_role;
