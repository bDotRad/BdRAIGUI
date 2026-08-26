## What was done

Brad asked for a graphical ("nice web GUI") representation of the
fleet, showing servers → specs, projects → agents, and (separately)
servers → apps/DB, plus web addresses for the apps. The Ecosystem tab
already existed with the fleet data as plain ASCII trees
(`.folder-tree` blocks) — this request was for a genuinely graphical
layout, not more text.

Added a new **"Fleet diagram"** section at the top of the Ecosystem tab
(`app/templates/index.html`), above the existing tree/table content
(left in place, unchanged, as the detailed text reference): a row of
bordered cards, one per server, built from the same target-fleet data
already in the tree —

- **BdRSrvDev** (this host): specs pill, a "Projects" list (each
  project as its own sub-card with its actual/planned agent chips
  underneath — same names/caveats as the tree), and an "Apps on this
  host" sub-card for the BdRDev dashboard itself (address
  `http://<pi-ip>:8420`, no DB).
- **BdRSrvAMI** / **BdRSrvDungeon** — rendered as dashed ("not
  provisioned yet") cards, each with an "Apps" sub-card per app showing
  DB (Supabase, where applicable) and web address (today's real address
  for PlanBdRad — `192.168.100.20`, still served by `PlanBdRadServer`
  — or "not deployed yet" for the others).
- **BdRBirdDetector** (physical Pi, 192.168.1.187): specs pill, one app
  card for the Streamlit GUI, address noted as local-network-only (no
  fixed URL documented), DB noted as not built yet (cloud DB is
  planned, per that project's own `Description.md`).

New CSS added (`.eco-diagram`, `.eco-server-card`, `.eco-project-card`,
`.eco-app-card`, `.eco-chip`, etc.) reusing the existing dark/theme
variables rather than introducing new colors. No backend/API changes —
this is static reference content, same as the tree it sits above, and
carries the same accuracy caveats (most of this is target layout, not
today's real state — see the existing "Not yet real" note still sitting
under the tree, which still applies to both sections).

Verified live: force-restarted `bdrdev-dashboard` (`kill -9` on the
running PID — `debug=False`/no autoreload, and SIGTERM doesn't trigger
systemd's `Restart=on-failure`) and confirmed via `curl localhost:8420/`
that the new "Fleet diagram" heading and all four server cards are
present in the served HTML.

**Outcome:** implemented, deployed, and verified live.

## Original request (verbatim)

READY

Add a tab called ECO.
This tab is a more graphical representation of the servers and the apps sitting below them including a DB if it has one and the web clients/addresses

I want to show

Server
 Specs

Projects
 <project>
  Agents

-------

Server
 Specs

Apps

DB
-----
