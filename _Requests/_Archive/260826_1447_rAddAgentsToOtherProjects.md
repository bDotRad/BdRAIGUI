## What was done

Follow-up to the same-day `rAgents` request that gave BdRDev its 4
generic agents. This request asked to check each of 5 other projects
for the agent set shown in the Ecosystem tab's target layout, and
create whatever's missing.

- **BdRAMAssist** — had only `asset-management-bulk-specialist`. Added
  `project-manager`, `web-dev-expert`, `supabase-sql-expert`,
  `doc-updater` as verbatim copies of BdRDev's generic templates (the
  project is Supabase/Vite-based, so they apply as-is). Updated
  `project-manager.md` to also route bulk asset-data work to the
  existing `asset-management-bulk-specialist`.
- **PlanBdRad** — already had real, domain-specific agents covering 3
  of the 4 (`project-manager`, `web-developer` = Web Dev Expert,
  `sql-developer` = Supabase SQL Expert), left untouched. Only
  `doc-updater` was missing (its `project-manager.md` explicitly
  documented "no dedicated docs-writer agent, I do it myself") — added
  the generic `doc-updater` and updated `project-manager.md`'s
  doc-keeping section and description to delegate to it instead.
- **BdRIS** — doesn't exist as a project under `~/projects/` yet, so
  there's nothing to add agent files to. Not treated as a blocker
  needing Brad's input (same conclusion as the earlier `rAgents` pass) —
  just not applicable until the project exists.
- **BdRBirdDetector** — already had 6 real, domain-specific agents
  (`pi-pipeline`, `sql-expert`, `esp32-nodes`, `db-webapp`,
  `docs-writer`, `docs-logs`) covering Web Dev Expert / SQL Lite Expert
  / ESP32 Expert / Doc Updater under different names — left untouched.
  The one genuine gap was **Project Manager**: nothing in this project
  owns `_Requests/` triage. Added `.claude/agents/project-manager.md`
  (flat file, matching this project's existing convention rather than
  the per-agent-folder shape) written around its actual 6-agent roster,
  the same way PlanBdRad's was. Noted in that file's body: as of
  today, `BdRBirdDetector` isn't in
  `BdRDev/state/selected_projects.json`, so there's no
  `proj-BdRBirdDetector` scheduler session actually driving this yet —
  flagged rather than silently added to the rotation, since that's a
  live scheduler behavior change outside what was asked.
- **BdRDungeon** — greenfield (scaffolded today, no `.claude/agents/`
  at all, tech stack undecided per its own `CLAUDE.md`). Added all 5
  named agents: the 4 generic templates verbatim (they don't assume a
  stack) plus a new `esp32-expert`, written the way BdRBirdDetector's
  `esp32-nodes` was when that project was equally greenfield — no
  firmware/protocol exists yet, don't invent the transport or
  framework, surface the choice instead. Updated the copied
  `project-manager.md` to route ESP32/field-device work to it.

Also updated the Ecosystem tab's "Not yet real, per current state" note
(`app/templates/index.html`) to stop saying BdRAMAssist/BdRDungeon have
no/partial agents and PlanBdRad/BdRBirdDetector's don't include a
project-manager — all now accurate. Dashboard restarted (`kill -9` on
`dashboard.py`, systemd relaunched it) and the new text verified live.

Committed and pushed in each of the 5 repos touched (BdRDev,
BdRAMAssist, PlanBdRad, BdRBirdDetector, BdRDungeon).

---

READY

Check for agent files. if they dont exist, create them


	BdRAMAssist
		Agents:
			- Project Manager
			- Web Dev Export
			- Supabase SQL Expert
			- Doc Updater
			
	PlanBdRad
		Agents:
			- Project Manager
			- Web Dev Export
			- Supabase SQL Expert
			- Doc Updater
			
	BdRIS
		Agents:
			- Project Manager
			- WEB Dev Export
			- Supabase SQL Expert
			- Doc Updater
			
	BdRBirdDetector
		Agents:
			- Project Manager
			- WEB Dev Export
			- SQL Lite Expert
			- ESP32 Expert
			- Doc Updater
			
	BdRDungeon
			- Project Manager
			- WEB Dev Export
			- Supabase SQL Expert
			- ESP32 Expert
			- Doc Updater
