## What was asked

Add a scheduler restart to the Admin tab too — previously it only had a
restart control for the `bdraigui-dashboard` service.

## What was found

Already done. `app/dashboard.py`, `app/common.py`, and `app/templates/index.html`
were modified (mtimes ~19:33-19:34) after this request file was created
(~19:31) — a concurrent session implemented it before this pass picked
the request up. See [[260822_1920_rClickReady]] for other recent
concurrent-edit context in this same working tree.

The implementation, verified by reading (not re-done):

- `app/templates/index.html`: Admin tab now has a second "Scheduler
  service" section with its own status badge and "Restart service"
  button (`admin-scheduler-status-row` / `admin-scheduler-restart-btn`),
  parallel to the existing dashboard one. `triggerSchedulerRestart()`
  confirms, POSTs `/api/admin/restart_scheduler`, then polls
  `/api/admin/status` until `scheduler_running` is true again.
- `app/dashboard.py`: new `_scheduler_pid()` (finds the running
  `scheduler.py` process via `pgrep -f`, anchored to end-of-line so a
  command merely mentioning the path isn't mistaken for the process)
  and `POST /api/admin/restart_scheduler`, which SIGKILLs that pid (not
  SIGTERM — same reasoning as the dashboard's own self-restart: systemd
  `Restart=on-failure` only relaunches on a non-clean exit).
  `/api/admin/status` now also reports `scheduler_needs_restart` and
  `scheduler_running`.
- `app/common.py`: new `scheduler_needs_restart()`, mirroring the
  existing `dashboard_needs_restart()` but reading the scheduler's own
  start time back from `state/scheduler_start.json` (written by the new
  `record_scheduler_start()`, since the dashboard is a separate process
  and can't just check its own `START_TIME`).
- `app/scheduler.py`: calls `common.record_scheduler_start()` once at
  startup to write that state file.

Read through both endpoints and the JS wiring end-to-end — no gaps
found (button disabling during `restarting`, badge states for
`not_running`/`requires_restart`/`restarting`, tab-header alert dot
reusing the same `needs-restart` class as the dashboard one).

## What changed

Nothing — the feature was already complete. Archiving this request so
it stops showing as outstanding.

## Outstanding — needs Brad

This is still uncommitted, alongside a large amount of other
already-uncommitted work in this working tree (`git diff --stat` shows
6 files, ~1000 lines changed, spanning several other archived requests
from today). Not restarting anything or committing as part of this
pass — just confirming the requested feature exists and archiving the
request. Whenever you're ready to pick up all of today's accumulated
changes:

```
sudo systemctl restart bdraigui-dashboard
sudo systemctl restart bdraigui-scheduler
```

---

Original request:

READY

Need to add the scheduler reboot too

sudo systemctl restart bdraigui-dashboard
sudo systemctl restart bdraigui-scheduler
</content>
