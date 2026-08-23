# 260822 — Archive panel: fix was already made, just never deployed

## Done

Brad reported the archive viewer's text panel was "still on the bottom."
The side-by-side fix from [[260822_1614_rArchivePanelLayout]] (`#archive-body`
flex row, list on the left / text panel on the right) was already sitting in
`app/templates/index.html` on disk — but the live `bdraigui-dashboard`
process (PID 90375) had started at 16:10:04, before that file was last saved
at 16:13:49, and Flask runs with `debug=False`/no autoreload. So the running
process was still serving the old stacked-layout template; the fix existed
but had never actually been picked up.

Per CLAUDE.md, forced a restart with `kill -9 90375` (SIGKILL counts as a
failure under `Restart=on-failure`, unlike plain SIGTERM) rather than waiting
on Brad's `sudo systemctl restart`. New process (PID 100039) came up within
~4s. Verified via `curl http://127.0.0.1:8420/` that the served HTML now
contains `#archive-body { display: flex; ... }` — the side-by-side layout is
live.

No code changes this pass — this was purely a "deploy the already-written
fix" issue. Worth noting for next time: a request marked done in the archive
isn't actually verified live unless someone confirms a restart happened
after the file was saved — [[260822_1614_rArchivePanelLayout]] left that
restart for Brad and it seems it never happened.

## Requested

READY

Panel is still on the bottom.
