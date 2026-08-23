## What was done

**Asked:** "Time is still out on the activity log."

**Found:** a prior fix ([260822_1408_r1_r2.md](260822_1408_r1_r2.md))
pinned the activity log's displayed time to bare `timeZone: 'UTC'` in
`renderLog()` (`app/templates/index.html`), specifically because letting
it fall back to the *viewing device's* timezone (phone/tablet over
Tailscale) produced garbage multi-hour offsets. That matched Brad's
wall-clock time at the time, when the offset was 0. It stayed wrong
this time, though, because "UTC" never observes DST — once Brad's local
time moved to BST (UTC+1) the log started reading an hour behind again,
same class of bug, new cause.

Asked Brad for the actual IANA timezone to pin to instead of guessing;
he confirmed **Europe/London**.

**Fix:** changed `timeZone: 'UTC'` to `timeZone: 'Europe/London'` in the
`toLocaleTimeString()` call in `renderLog()`. This still avoids trusting
the viewing device's clock/timezone (the original bug this whole
mechanism exists to dodge), but now tracks GMT/BST correctly across DST
transitions instead of drifting an hour off every summer.

**Outcome:** fixed and deployed (dashboard restarted via
`POST /api/admin/restart`, no sudo needed) and verified live via
`curl` that the rendered page now carries `timeZone: 'Europe/London'`.
Committed and pushed.

---

## Original request (verbatim)

READY

Time is still out on the activity log
