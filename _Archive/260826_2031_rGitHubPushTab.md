## What was done

Added a "GitHub" section to each project's detail page (`/project/<name>`),
shown only for projects whose git `origin` remote resolves to GitHub
(covers both `https://github.com/...` and the per-project SSH host-alias
form like `git@github.com-bdrdev:...` used on this fleet).

The section has:
- A changed-files readout (from `git status --porcelain`), so you can see
  what you're about to commit.
- A commit-message box and a **Commit & Push** button. Since the request
  was titled "GitHub Push" (even though the body only said "commit"), the
  button does `git add -A` → `git commit` → `git push` as one action,
  rather than just a local commit -- that's what actually gets changes
  onto GitHub, which seemed to be the point of the tab. Flags a clean
  working tree instead of erroring, and shows the git output either way.
- A "Version history" table below it (`git log`, last 30 commits: short
  hash, relative date, subject line).

**Files changed:**
- `app/common.py` -- new helpers: `has_github_remote`, `git_status`,
  `git_log`, `git_commit_and_push`. All git calls use `subprocess.run`
  with argument lists (never `shell=True`, never string-interpolated),
  so the commit message can't be used for command injection.
- `app/dashboard.py` -- `has_github` added to the existing
  `/api/project/<project>/files` response; three new routes:
  `GET /api/project/<project>/git/status`, `GET .../git/log`,
  `POST .../git/commit`. All validate `project` against
  `common.list_projects()` like every other per-project route.
- `app/templates/project.html` -- the new GitHub section/JS, hidden by
  default and shown only when `has_github` comes back true.

**Verification:** syntax-checked both Python files, ran `dashboard.py`
standalone on a scratch port against the real `~/projects` tree and
confirmed `/project/BdRDev`, `/api/project/BdRDev/git/status`, and
`.../git/log` return correct live data with `has_github: true`; confirmed
a non-GitHub project gets `has_github: false` and the section stays
hidden. The full commit/push flow was exercised only against a throwaway
repo in `/tmp` -- confirmed add+commit+push succeeds and reports output,
a clean tree returns a clear "nothing to commit" message, and an empty
message is rejected. No commit or push touched any real project during
testing.

**Outcome:** code change complete and verified standalone, but **not yet
live** -- `bdrdev-dashboard` runs with `debug=False` and no autoreload, so
this won't take effect until the service is restarted
(`sudo systemctl restart bdrdev-dashboard`, or a SIGKILL to force
systemd's `Restart=on-failure` to pick it up) -- no sudo available in this
session, so that step is left for Brad.

---

READY

Add a GIthub tab for each project if it has github.
Have a commit message and a button to commit.
Then below have the version history
