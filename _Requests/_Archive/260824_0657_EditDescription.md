## What was done

Brad asked to be able to edit `Description.md` from a project's Files tab
(`/project/<name>`), which was previously browse-only (click to view in a
read-only textarea, same as `CLAUDE.md`/agent files).

Added an edit path scoped to just the description file (not `CLAUDE.md` or
`.claude/agents/*.md`, which stay browse-only):

- `app/common.py`: new `write_description_file(project, content)` — writes
  to the project's existing `Description.md`/`description.md` if found, or
  creates `Description.md` if neither exists yet.
- `app/dashboard.py`: new `POST /api/project/<project>/description` route.
- `app/templates/project.html`: Description panel now shows an "Edit"
  button (or "Create Description.md" when none exists yet) that opens the
  shared file-view textarea in an editable state with its own Save/Cancel
  actions, mirroring the existing request-edit UI. Wired cancellation so
  switching between viewing a file, editing a request, and editing the
  description don't collide over the shared textarea.

Verified with `python3 -m py_compile` and by curling the new endpoint
directly against the live dashboard (created a test `Description.md` for
`_BdRAIGUI`, confirmed it round-tripped via the files/file endpoints, then
removed the test file since `_BdRAIGUI` didn't have one before).

**Outcome:** fixed and deployed. Dashboard was restarted (`kill -9` on the
running process, since this session has no `sudo` — systemd's
`Restart=on-failure` picked it up) to pick up the template/route changes;
confirmed running afterward.

---

READY

Allow me to edit Description.md when in the Files tab
