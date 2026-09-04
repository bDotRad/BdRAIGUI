# New web test environment — BdRWebGUIDev

**Processed:** 2026-09-04 10:25 · **Outcome:** new project created,
scaffolded, starter page built, pushed to GitHub. Deploy-key install +
`sudo` service install handed back to Brad (see below).

## What was asked

Create a new project `BdRWebGUIDev` on the dev server "with all the
required folders" — a web GUI showcase (colours, shapes, layouts,
typography) that also doubles as a front-end sandbox. Brad had already
created the empty `bDotRad/BdRWebGUIDev` repo on GitHub. Wanted the
deploy key handed back so he could set up access himself, and a simple
starter page "similar to bdrpisrvdev" but with generic labels
("Tab 1", "Text Size 10 Arial Bold"). Use a showcase standard if one
exists, but keep it simple.

## What was done

New repo at `~/projects/BdRWebGUIDev`, `git init` + first commit
(`7defb8c`), pushed to `https://github.com/bDotRad/BdRWebGUIDev.git`
via the account-level `gh` HTTPS credential helper.

**Standard project shape** (per `_Instructions/ProjectSetup.md`):

- `CLAUDE.md` — agent notes: points at the fleet Layer-1 standards
  (not copied), records the project gotchas (no sudo, no autoreload,
  port 8430, git-SHA version, "keep it simple").
- `Description.md` — human summary + `## Git repository` section.
- `.claude/agents/` — BdRDev's four generic agents copied in as the
  starting set (project-manager, web-dev-expert, supabase-sql-expert,
  doc-updater).
- `References/README.md` — placeholder explaining the folder.
- `_Instructions/README.md` — states this is the Layer-2 folder and
  there are no deviations from Layer 1 yet.
- `_Requests/_Archive/` — created (with `.gitkeep`).

**Starter app** — deliberately tiny:

- `app/webgui.py` — Flask, one route `/`, `debug=False`. `app_version()`
  = `git rev-parse --short=7 HEAD`, cached. Serves on `:8430`.
- `app/templates/index.html` — the whole page, all CSS inline. Dark
  fleet palette from `_Instructions/WebUI.md`. Header with title +
  7-char SHA version; four tabs — **Tab 1** typography samples
  (labelled "Text Size 10 Arial Bold" etc.), **Tab 2** colour swatches
  + status colour-coding, **Tab 3** shapes (square / rounded / circle /
  pill / outline / shadow / triangle), **Tab 4** layout patterns
  (auto-fit grid, two-column, sidebar, stack). Vanilla-JS tab switch.
- `requirements.txt` (just Flask), `run.sh`, `systemd/bdrwebguidev.service`,
  `README.md`, `.gitignore`.

Verified: `./run.sh` builds the venv, app returns HTTP 200 on `:8430`,
page renders all four tabs and the version string.

**Deploy key** — generated `~/.ssh/bdrdev_to_bdrwebguidevgit` on this
box (comment `BdRDev-to-BdRWebGUIDevGIT`, per `_Instructions/SSH.md`),
`.pub` verified against `ssh-keygen -y`. The `~/.ssh/config` alias edit
was blocked by the unattended session's classifier, so that plus the
GitHub deploy-key install and the `sudo` service install are written as
an Action block in **`BdRWebGUIDev/_Requests/rProject Setup.md`**
(first line `WAITING RESPONSE`), which also carries the public key for
Brad to paste.

## Not done / left for Brad

Everything in `BdRWebGUIDev/_Requests/rProject Setup.md`:
1. Add the deploy key under the repo's Settings → Deploy keys (write).
2. Append the `github.com-bdrwebguidev` block to `~/.ssh/config`.
3. `git remote set-url origin` to the SSH alias.
4. `sudo` install + start `bdrwebguidev.service` (port 8430).
5. Optional: tick "BdRWebGUIDev" into the BdRDev scheduler rotation on
   the dashboard.

No nginx reverse-proxy was set up — reachable at `:8430` directly for
now, since the request only said "remain on the Dev server".

---

## Original request (verbatim)

```
READY

Make a new project with all the required folders.
The project is called BdRWebGUIDev

The purpose is the showcase lots of types of web gui config, colours, shapes layouts etc.

It also lets me try new things.

It will remain on the Dev server. I have created BdRWebGUIDev in github.

Give me the deploy key and ill set up the access.

Start by making a simple web page similar to bdrpisrvdev.

Except just call things generic like Tab 1, Tab 2, Text Size 10 Arial Bold.

If there is a starndard for show casing web pages use that but I waant it simple too.
```
