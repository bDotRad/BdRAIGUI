## What was done

Two requests processed together in one pass.

### rRestart — debounce the "needs restart" flag

**Issue:** the Admin tab's restart flag was flapping — Brad clicks
"Restart service," it comes back up, and almost immediately flags
"Requires Restart" again, even though nothing new had actually changed.

**Cause:** `dashboard_needs_restart()` / `scheduler_needs_restart()`
compared the newest watched-file mtime to the process's start time with
no slack. A Claude session editing its own `app/*.py`/`templates/`/
`static/` files typically saves several of them in a row over a few
seconds — each save nudges the watched mtime forward again, so if the
restart button was clicked mid-edit-batch, the freshly-restarted
process's start time could still land *before* a save that followed
moments later, re-tripping the flag.

**Fix:** found already implemented (uncommitted) in `app/common.py` when
this pass started — added `RESTART_DEBOUNCE_SECONDS = 5` and changed
both functions to require the newest watched mtime to be at least 5s
old before reporting `needs_restart`. This lets a whole edit batch
settle before the flag fires once, instead of flapping true/false/true
as each file save lands.

Verified: `py_compile` clean on `common.py`/`dashboard.py`/`scheduler.py`;
exercised the debounce window directly (touch a watched file, confirm
`needs_restart` is `False` immediately after and `True` once 5s+ have
elapsed). Deployed live via `POST /api/admin/restart` (no sudo needed —
that endpoint SIGKILLs the dashboard's own process, which systemd's
`Restart=on-failure` picks back up) and confirmed via
`GET /api/admin/status` that the flag correctly cleared to `false`
after the restart picked up the new code.

### rTitle Bar — remove "tick projects" hint text

**Issue:** the subtitle under the header ("Tick projects to add them to
the rotation. The scheduler handles switching automatically.") was
asked to be removed, with that info moved to Help instead.

**Found:** the Help page (`/help`) already documents this under
"Project card" → **Active/Inactive**: "Whether this project is in the
scheduler's rotation pool. Active projects get woken automatically when
they have Ready requests; Inactive ones are skipped." — and the Help
link sits right next to where the subtitle was. No new Help content
needed.

**Fix:** removed the `.subtitle` `<div>` from `app/templates/index.html`
(and its now-unused CSS rule). Verified via `curl` against the live
site after the same restart above — the subtitle text no longer appears
in the rendered page.

**Outcome:** both fixed, deployed live, and verified. Committed and
pushed.

---

## Original requests (verbatim)

### rRestart.md

READY

Often it tells me to click restart gui. I do and it starts running then
it needs another restart. Maybe hold off flagging a restart until its
finished. Or do you need to check something

### rTitle Bar.md

READY

Remove the text saying to tick projects etc. that can go in to help
