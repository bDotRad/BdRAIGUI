## What was done

Brad noticed that on a project's Files tab, the only file showing up was
`CLAUDE.md` -- and flagged that this shouldn't be treated as the
project's description, since `CLAUDE.md` is written for the Claude Code
agents the scheduler wakes, not as a human-facing summary.

Checked `app/common.py`/`app/templates/project.html`: the Description
panel and the "Claude agent files" panel (`CLAUDE.md` +
`.claude/agents/*.md`) were already kept fully separate in the UI (this
was the point of the prior `EditDescription` request) -- `_BdRAIGUI`
just didn't have a `Description.md` yet, so its Description panel was
showing the empty "No Description.md found" state while `CLAUDE.md`
appeared under the agent-files list below it. No code bug.

Created `Description.md` at the repo root with a short, human-facing
summary of what BdRAIGUI is and how it's used (dashboard + scheduler,
how requests get picked up) -- distinct from `CLAUDE.md`'s agent-facing
operating notes. Verified via `GET /api/project/_BdRAIGUI/files` against
the live dashboard: `description` now points at `Description.md` and
`agent_files` lists `CLAUDE.md` separately, as intended.

**Outcome:** fixed, no restart needed (static file, no code change).

---

READY

Create and update the description file. I think there is a Claude File. It shouldnt be that, thats for the agents
