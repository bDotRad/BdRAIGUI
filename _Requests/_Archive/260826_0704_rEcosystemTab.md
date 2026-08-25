## What was done

Brad asked for an "Ecosystem" tab showing the structure of devices and
the generic structure of folders.

Added a new **Ecosystem** tab to the dashboard (`app/templates/index.html`),
alongside Projects / Activity Log / Admin, with two static reference
sections:

- **Devices** — a table of the fleet's machines, sourced from
  `_Instructions/SSH.md`: `BdRDev` (this host, runs the dashboard/scheduler
  and local projects), `PlanBdRadServer` (VM, 192.168.100.20, runs
  PlanBdRad), `BdRadBirdDetector` (physical Pi, 192.168.1.187, runs
  BdRBirdDetector).
- **Generic project folder structure** — the standard tree from
  `_Instructions/ProjectSetup.md` (`CLAUDE.md`, `Description.md`,
  `.claude/agents/<slug>/<slug>.md`, `References/`), same content
  already answered once before in `260825_0811_rStandardTree.md`.

This is static reference content (matches how the request framed it --
"shows the structure", not live fleet telemetry), styled to match the
existing Admin panel. No backend/API changes needed.

Verified live: dashboard process had already been restarted (~06:59,
not by this session) so the change was served immediately -- confirmed
via `curl` that the new tab button and both sections render.

**Outcome:** implemented and verified live.

---

READY

Can you make a tab Ecosystem which shows the structure of devices, and the generic structure of folders
