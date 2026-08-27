# Help for Retards tab

**Asked:** Add a second help page next to the existing "Help" link,
aimed at a non-technical friend, explaining the system in plain terms:
servers, the DEV application, project folders + READY/Waiting Input,
GitHub push/pull, how apps run on the servers, and how the Claude
agents/sessions work.

**Done:**

- New template `app/templates/help_simple.html` — same dark styling as
  `help.html`, six plain-English sections plus a "whole loop in one
  breath" summary. Written mate-to-mate, no jargon, each section ends
  with a one-line TL;DR. Server names / roles taken from the Ecosystem
  tab (BdRSrvDev = dev/workbench, BdRPiAMI = Raspberry Pi running the
  finished apps, BdRBirdDetector). Agent list (Project Manager, Web Dev
  Expert, Supabase SQL Expert, Doc Updater) and the Independent Claude
  session described from `CLAUDE.md`. Push-only app servers +
  build-on-dev-then-pull flow from `_Instructions/AppServerSync.md`.
- `app/dashboard.py` — new route `GET /help-simple` rendering that
  template, right after the `/help` route.
- `app/templates/index.html` — second `<a class="help-link">` in the
  `#tabs` bar labelled "Help for Retards" pointing at `/help-simple`;
  added `#tabs .help-link-extra { margin-left: 0; }` so it sits next to
  "Help" rather than each grabbing `margin-left:auto`.

**Verified:** dashboard process is serving the new code —
`GET /help-simple` returns 200 and renders, `GET /` shows the new link.
(The process had already picked up a restart by the time verification
ran; no manual restart step was needed from this pass. If the live
dashboard ever shows only the old single "Help" link, hit Admin →
Restart service.)

---

READY

I have a dum ass saffa mate whom i want to explain how my system works.

Can you do it in simple terms from
Servers
DEV Application
How the project folders work and the READY/Waiting Input

Github push pull

How the Apps work on the Servers

include how the claude agents and sessions work.

Add a new tab next to help called help for retards
