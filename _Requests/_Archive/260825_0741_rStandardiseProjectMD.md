## What was done

Brad wanted (1) a standard shape for project MD files/folders and (2)
a "Setup Project" shorthand trigger so he doesn't have to spell out
"create the files and folders, populate the description" each time.

Wrote `_Instructions/ProjectSetup.md` (same "canonical copy lives here"
pattern as `BdRAIGUI.md`/`SSH.md`) documenting the standard, based on
what had already organically emerged rather than inventing something
new:

- `CLAUDE.md` (root) — agent-facing, already established.
- `Description.md` (root) — human-facing, already established (see
  `260824_1712_CreateDescription.md`); confirmed via `app/common.py`
  (`find_description_file`, `DESCRIPTION_FILENAMES`).
- `.claude/agents/<slug>/<slug>.md` — one folder per subagent, standard
  Claude Code subagent frontmatter. This shape already existed on
  `PlanBdRad` (`project-manager`, `web-developer`, `sql-developer`,
  `asset-management-guru`) and matches what `list_agent_files()`
  globs for (`.claude/agents/**/*.md`), so kept it rather than the
  flatter "Claude xxx Agent.md" naming floated in PlanBdRad's original
  `Description.md` draft.
- `References/` (root, new) — plain folder for site-specific/external
  docs Brad drops in by hand; not parsed by any tooling.

Didn't add a separate "Project Details" wrapper folder Brad had floated
as one option -- `Description.md` living at repo root is already the
established, dashboard-recognized convention, and a wrapper folder
would just add indirection without a use.

Applied the standard immediately to `BdRAMAssist`, which was already
sitting in `_BdRAIGUI/state/selected_projects.json` (in the scheduler
rotation) but was otherwise an empty directory (no git repo, no files
at all):

- `Description.md` — states its purpose (helping populate PlanBdRad,
  handling bulk asset-management data work) per the request body.
- `References/README.md` — placeholder explaining the folder's purpose
  (empty otherwise, per Brad's ask).
- `.claude/agents/asset-management-bulk-specialist/asset-management-bulk-specialist.md`
  — the one agent Brad asked for by name ("Asset Management specialist
  in bulk handling"). Scoped it as a hands-on bulk-data-processing role
  (import/clean/map at volume, `tools: Read, Write, Edit, Bash, Grep,
  Glob`) and explicitly distinguished it from PlanBdRad's own
  `asset-management-guru`, which is a read-only maintenance-strategy
  advisor -- the two shouldn't overlap.

Out of scope, deliberately: didn't `git init` BdRAMAssist, write it a
`CLAUDE.md`, or otherwise bootstrap it as a working app -- the request
was specifically about the MD-file/folder standard, and `ProjectSetup.md`
says as much (scoped to file layout, not git/systemd/tech-stack setup).
That's real follow-on work for a future request once Brad decides
BdRAMAssist's actual tech stack.

**Outcome:** done. No code/app changes, no restart needed -- this
touched `_BdRAIGUI/_Instructions/` (a new convention doc) and
`BdRAMAssist/` (a different project's directory on the same Pi, not
`_BdRAIGUI`'s own app code).

---

READY

Id Like to standardise Project MD files.
And Id like to have a standard project setup process.

Maybe a folder called Project Details, the Description.MD, Agents folder, References (if you have a better idea put it forward)

Setup Project

*Instead of this*
Setup the project file with all the relevant firls and folders
Populate the Description .md

*I just want to say Setup Project as the title*



Description
This project is used to help populate PlanBdR.

Agents
I require at least one agent that is an Asset Management specialist in bulk handling.

Additional
Make a folder called References that I can place site specific documentation in.
