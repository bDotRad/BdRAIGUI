## What was done

Added a single "Restart both services" button to the Admin tab
(`app/templates/index.html`), above the existing separate Dashboard/
Scheduler restart controls. It triggers both `/api/admin/restart` and
`/api/admin/restart_scheduler` (both already existed, used by the
separate buttons) and reuses the existing status-polling/rendering
functions (`renderAdminStatus`, `renderSchedulerStatus`,
`adminRestarting`, `schedulerRestarting`) so both status badges update
live during the restart, same as the individual buttons.

No backend changes needed -- both endpoints already existed.

**Verification:** the dashboard service had already been restarted
(`kill -9` on the running PID, per the no-sudo/no-autoreload convention
in this project's CLAUDE.md) since this change was made, so the new
button was already live. Confirmed via `curl localhost:8420/ | grep
admin-restart-both-btn` that it's present in the served HTML.

**Outcome:** implemented, deployed, and verified live. Committed
(`772612f`).

## Original request (verbatim)

READY

Add a single button to reboot both services Dashboard and Scheduler
