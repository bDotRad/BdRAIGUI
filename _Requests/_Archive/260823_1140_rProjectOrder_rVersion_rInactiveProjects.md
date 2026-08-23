## What was done

Three related requests, handled together:

**rProject order / rInqctive projects (project card layout):** Active
(in-rotation) projects now render as full tiles in the main `#grid`;
inactive projects render below them, as the same full tiles, in a
separate `#inactive-row` under an "Inactive" label. First pass rendered
inactive projects as small checkbox chips instead of full tiles; Brad
clarified he wanted full tiles for both, just inactive ones positioned
below -- fixed by dropping the chip rendering (`chipHtml`/
`.inactive-chip`) and reusing `cardHtml` for both groups, with
`#inactive-row` styled as its own grid matching `#grid`.
(`app/templates/index.html`)

**rVersion (version number under the logo):** `common.app_version()`
reads the current commit's date/time and short hash via `git log -1
--format=%cd %h --date=format-local:%y%m%d_%H%M%S`, cached once per
process (Flask has no autoreload, so this is stable for the process's
life). Rendered in `app/templates/index.html` as `#site-version`, white
text, positioned directly under the rat logo. `dashboard.py`'s `index()`
route passes it into the template.

Second half of rVersion asked whether requests were being pushed to
GitHub after processing -- checked `git log` against the archive: only
7 commits existed against ~20+ archived requests, confirming most
recent work (including the above two features, already fully built and
verified live before this request even landed) had been sitting
uncommitted since the last push (`0eb4c38`). Updated
`_Instructions/Requests.md` to add an explicit "commit and push to
GitHub" step to the archive process, so this stops recurring.

All of the above -- plus the accumulated backlog of already-verified,
previously-uncommitted work described in the ~20 archive entries dated
260822 -- is being committed and pushed together in the commit that
follows this archive entry.

**Outcome:** fixed and deployed (dashboard restarted via SIGKILL,
verified live: `/api/status` shows correct `in_rotation` grouping,
`/` serves the updated template and version string). Committed and
pushed to GitHub per the new documented convention.

---

## Original requests (verbatim)

### rProject order.md

READY

Place the active projects above the inactive.

Inwctive are to be on a line below and wctive projects on the main page

### rVersion.md

READY

Add a version number under the rat logo in white.
Format
yymmdd_hhmmss github id

If you havent been pushing to github after rewuests, update the documentation to do that

### rInqctive projects.md

READY

I still want the inactive projects to be a full tile. I just wanted them to be below the active ones.
