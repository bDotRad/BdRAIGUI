-- ============================================================================
-- BdRDev fleet / ecosystem seed
-- ----------------------------------------------------------------------------
-- Loads every row from state/ecosystem.json (as of 2026-08-28) into the
-- schema from 20260828120000_fleet_schema.sql.
--
-- Idempotent: entity tables upsert on their natural key, link/child tables
-- use ON CONFLICT DO NOTHING / DO UPDATE. Re-running realigns the seeded
-- rows to these values; it never duplicates.
--
-- Note: "SQL Lite" in the source JSON is the software "SQLite" here; the
-- server's free-text string keeps the original "Nginx . SQL Lite" wording.
-- ============================================================================

-- ---------------------------------------------------------------------------
-- software catalogue
-- ---------------------------------------------------------------------------
insert into public.software (name, description) values
  ('Claude Code', 'Anthropic Claude Code CLI / agent sessions'),
  ('Nginx',       'Reverse proxy and TLS termination'),
  ('Supabase',    'Self-hosted Supabase stack (Postgres 17, PostgREST, Auth, Studio)'),
  ('SQLite',      'Embedded file-based SQL database'),
  ('Scheduler',   'BdRDev round-robin Claude Code session scheduler'),
  ('Firebase',    'Google Firebase cloud sync / realtime database')
on conflict (name) do update set description = excluded.description;

-- ---------------------------------------------------------------------------
-- servers
-- ---------------------------------------------------------------------------
insert into public.servers
  (name, tag, address, host, os, ram, disk, software_freetext, git_notes, provisioned, dev_host, sort_order)
values
  ('BdRVSrvDev', 'this host, local', '192.168.100.10', 'VM', 'Ubuntu Server', '8GB', '512GB SSD',
   'Claude Code · Nginx · Scheduler',
   $g$GitHub
Push to bDotRad/: BdRDev, BdRAMAssist, PlanBdRad, BdRIS, BdRBirdDetector, BdRDungeon
Pull from bDotRad/: BdRDev$g$,
   true, true, 1),

  ('BdRPiAMI', 'Raspberry Pi 8GB, 10.10.10.20', '10.10.10.20', 'Raspberry Pi', 'Raspberry Pi', '8GB', '',
   'Claude Code · Nginx · Supabase',
   $g$GitHub
Pull from bDotRad/: BdRAMAssist, PlanBdRad, BdRIS$g$,
   true, false, 2),

  ('BdRSrvDungeon', 'not provisioned yet', '', 'VM', 'Ubuntu Server', '4GB', '256GB SSD',
   'Claude Code · Nginx · Supabase',
   $g$GitHub
Pull from bDotRad/: BdRDungeon$g$,
   false, false, 3),

  ('BdRBirdDetector', 'physical Pi, 192.168.1.187', '192.168.1.187', 'Raspberry Pi', 'RPI OS Lite', '4GB', '64GB SD Card',
   'Nginx · SQL Lite',
   $g$GitHub
Pull from bDotRad/: BdRBirdDetector
Firebase
Push$g$,
   true, false, 4)
on conflict (name) do update set
  tag               = excluded.tag,
  address           = excluded.address,
  host              = excluded.host,
  os                = excluded.os,
  ram               = excluded.ram,
  disk              = excluded.disk,
  software_freetext = excluded.software_freetext,
  git_notes         = excluded.git_notes,
  provisioned       = excluded.provisioned,
  dev_host          = excluded.dev_host,
  sort_order        = excluded.sort_order;

-- ---------------------------------------------------------------------------
-- server_software (M:N)
--   Tracked booleans in the source JSON: BdRVSrvDev claude+nginx;
--   BdRPiAMI claude+nginx+supabase; BdRSrvDungeon claude+nginx+supabase;
--   BdRBirdDetector nginx+sqlite. Scheduler / Firebase added from the
--   free-text + git notes for the same boxes.
-- ---------------------------------------------------------------------------
insert into public.server_software (server_id, software_id)
select s.id, sw.id
from (values
  ('BdRVSrvDev',      array['Claude Code', 'Nginx', 'Scheduler']),
  ('BdRPiAMI',        array['Claude Code', 'Nginx', 'Supabase']),
  ('BdRSrvDungeon',   array['Claude Code', 'Nginx', 'Supabase']),
  ('BdRBirdDetector', array['Nginx', 'SQLite', 'Firebase'])
) as v(server_name, software_names)
join public.servers  s  on s.name = v.server_name
join public.software sw on sw.name = any (v.software_names)
on conflict (server_id, software_id) do nothing;

-- ---------------------------------------------------------------------------
-- projects
-- ---------------------------------------------------------------------------
insert into public.projects (name, exists_flag, sort_order) values
  ('BdRDev',          true,  1),
  ('BdRAMAssist',     true,  2),
  ('PlanBdRad',       true,  3),
  ('BdRIS',           false, 4),
  ('BdRBirdDetector', true,  5),
  ('BdRDungeon',      true,  6)
on conflict (name) do update set
  exists_flag = excluded.exists_flag,
  sort_order  = excluded.sort_order;

-- ---------------------------------------------------------------------------
-- project_agents
-- ---------------------------------------------------------------------------
insert into public.project_agents (project_id, agent_name, sort_order)
select p.id, a.agent_name, a.ord
from (values
  ('BdRDev',          'Project Manager',     1),
  ('BdRDev',          'Web Dev Expert',      2),
  ('BdRDev',          'Supabase SQL Expert', 3),
  ('BdRDev',          'Doc Updater',         4),
  ('BdRAMAssist',     'Project Manager',     1),
  ('BdRAMAssist',     'Web Dev Expert',      2),
  ('BdRAMAssist',     'Supabase SQL Expert', 3),
  ('BdRAMAssist',     'Doc Updater',         4),
  ('PlanBdRad',       'Project Manager',     1),
  ('PlanBdRad',       'web-developer',       2),
  ('PlanBdRad',       'sql-developer',       3),
  ('BdRBirdDetector', 'Project Manager',     1),
  ('BdRBirdDetector', 'Web Dev Expert',      2),
  ('BdRBirdDetector', 'sql-expert',          3),
  ('BdRBirdDetector', 'esp32-nodes',         4),
  ('BdRBirdDetector', 'docs-logs',           5),
  ('BdRDungeon',      'Project Manager',     1),
  ('BdRDungeon',      'Web Dev Expert',      2),
  ('BdRDungeon',      'Supabase SQL Expert', 3),
  ('BdRDungeon',      'ESP32 Expert',        4),
  ('BdRDungeon',      'Doc Updater',         5)
) as a(project_name, agent_name, ord)
join public.projects p on p.name = a.project_name
on conflict (project_id, agent_name) do update set sort_order = excluded.sort_order;

-- ---------------------------------------------------------------------------
-- apps
-- ---------------------------------------------------------------------------
insert into public.apps (name, server_name, server_id, tag, web_address, db, planned, sort_order)
select v.name, v.server_name, s.id, v.tag, v.web_address, v.db, v.planned, v.sort_order
from (values
  ('BdRDev dashboard + scheduler', 'BdRVSrvDev',      '',                                  'http://192.168.100.10:8420',      'none (JSON state files)',      false, 1),
  ('PlanBdRad',                    'BdRPiAMI',        'today: runs on PlanBdRadServer',    '10.10.10.20',                     'Supabase (Postgres)',          false, 2),
  ('BdRAMAssist',                  'BdRPiAMI',        '',                                  'not deployed yet',                'none — feeds PlanBdRad''s DB',  false, 3),
  ('BdRIS',                        'BdRPiAMI',        'project doesn''t exist yet',        '',                                '',                             true,  4),
  ('BdRDungeon',                   'BdRSrvDungeon',   '',                                  'not deployed yet',                'Supabase (planned)',           false, 5),
  ('BdRBirdDetector',              'BdRBirdDetector', 'edge/gui.py — Streamlit',           'local network only, no fixed URL', 'none yet — cloud DB planned',   false, 6)
) as v(name, server_name, tag, web_address, db, planned, sort_order)
left join public.servers s on s.name = v.server_name
on conflict (name) do update set
  server_name = excluded.server_name,
  server_id   = excluded.server_id,
  tag         = excluded.tag,
  web_address = excluded.web_address,
  db          = excluded.db,
  planned     = excluded.planned,
  sort_order  = excluded.sort_order;

-- ---------------------------------------------------------------------------
-- fleet_meta (notes blob, verbatim from state/ecosystem.json)
-- ---------------------------------------------------------------------------
insert into public.fleet_meta (id, notes) values (1,
$notes$Not yet real, per current state: BdRSrvDungeon isn't provisioned yet. BdRPiAMI (formerly the PlanBdRadServer VM; now a physical Raspberry Pi 8GB at 10.10.10.20) is real and reachable — it currently runs PlanBdRad, with BdRAMAssist's repo cloned there too (not yet confirmed running as a deployed service). This host (BdRVSrvDev, 192.168.100.10) is real; its machine hostname is still BdRDev — the rename to the BdRVSrv… / BdRPiSrv… convention (VM vs Raspberry Pi) is display-only in this data so far, not yet applied to the actual hostname / SSH key names / systemd units. BdRIS doesn't exist as a project yet. BdRDev, BdRAMAssist, and BdRDungeon now have all the agents shown above for real, under .claude/agents/ (BdRDev's set is written generically so it doubles as the copyable template for other projects — see _Instructions/ProjectSetup.md). PlanBdRad and BdRBirdDetector have equivalent agents under different, domain-specific names rather than the generic names shown here — both now also have a real project-manager. None of the named agents exist for BdRIS, since the project itself doesn't exist. Deploy-key conventions: _Instructions/SSH.md.$notes$
)
on conflict (id) do update set notes = excluded.notes;

-- Ask PostgREST to reload its schema cache so the new tables / view are
-- exposed on the REST API immediately (no-op if pgrst isn't listening).
notify pgrst, 'reload schema';
