# 260822 — Per-project detail page (Description + Claude agent files)

## Done

Added `app/templates/project.html`, served at `GET /project/<project>`,
showing:

- **Project name** as the page title/heading.
- **Description** — `common.find_description_file()` looks for
  `Description.md`/`description.md` at the project root and shows it as
  a clickable entry (empty-state message if none exists).
- **Claude agent files** — `common.list_agent_files()` collects the
  project's root `CLAUDE.md` (if present) plus every `.md` under
  `.claude/agents/`.
- Clicking any listed file loads it read-only into a textarea via
  `GET /api/project/<project>/file?path=...` (`common.read_project_file`),
  which only serves paths that are exactly the description file or one
  of the listed agent files — not an arbitrary path under the project.
- Linked from each card on the dashboard via a new "Files" link
  (`app/templates/index.html`).

Verified via Flask test client: `/project/<name>` renders 200,
`/api/project/<name>/files` returns the expected shape (tested against
this project, which currently has neither a `Description.md` nor agent
files, so both come back empty — that's the correct empty-state, not a
bug).

## Requested

READY

For each project I would like a page that has
Project Name
Description.md file
Claude Agent Files (.md)

A read only text interface would be good for each one, or the ability to open each file
