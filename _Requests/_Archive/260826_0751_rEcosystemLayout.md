## What was done

Request asked for a tree of the servers/software/projects to be added
to the Ecosystem tab, on the left, with the existing "Generic project
folder structure" tree moved to the right.

Mid-task Brad added a follow-up ("under the Claude entry, list the
Agents") asking for each project's Claude Code subagents to be listed
under its line in the new tree.

Changes in `app/templates/index.html`:
- New `.ecosystem-row` flex layout (two columns, wraps on narrow
  screens) replacing the old single-column stack; `#ecosystem-panel`
  widened from `max-width: 720px` to `1120px` to fit both columns.
- New left-hand block "Servers → software / projects": a plain-text
  tree (reusing the existing `.folder-tree` style) showing the three
  known devices (BdRDev, PlanBdRadServer, BdRadBirdDetector) and what
  runs on each, with each BdRDev-hosted project's `.claude/agents/`
  subagents listed underneath it (enumerated via `find` against each
  project's actual `.claude/agents/` folder, not guessed).
- The existing "Generic project folder structure" block moved
  unchanged into the right-hand column of the same row.
- The "Devices" table block above stays full-width, untouched.

Verified live: force-restarted `bdrdev-dashboard` (`kill -9` on the
main PID -- `debug=False`/no autoreload means template edits don't
take effect otherwise, and SIGTERM wouldn't trigger systemd's
`Restart=on-failure`) and confirmed via `curl localhost:8420/` that
the served HTML matches the edited template.

Outcome: done, deployed, verified.

## Original request (verbatim)

READY

Can you add the tree structure of the severs, Software, and projects

Add to the left side, then move the folder structure to the right
