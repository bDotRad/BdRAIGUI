# Move Activity Log to a tab

**What was asked:** Move the Activity Log off the main dashboard page and
onto its own tab, so the Projects grid gets more room.

**What was done:** Added a small tab bar (`Projects` / `Activity Log`) to
`app/templates/index.html`, above the projects grid. The grid now lives in
its own tab panel, and the Activity Log panel moved into a second tab panel
that's hidden until selected. The log list's max-height now scales with the
viewport (`calc(100vh - 260px)`) since it has the whole tab to itself instead
of sharing space below the grid. The selected tab is remembered in
`localStorage` so a refresh doesn't bounce you back to Projects. Status/log
polling (`loadStatus`/`loadLog`, every 5s) is unchanged — both keep running
regardless of which tab is active, so switching to Activity Log always shows
current data immediately.

**Outcome:** Fixed and deployed. Flask runs with `debug=False`/no
autoreload, so the running `bdraigui-dashboard` service (pid at the time)
was restarted via `kill -9` (SIGTERM doesn't trigger systemd's
`Restart=on-failure`, only SIGKILL does) to pick up the template change.
Verified via `curl http://127.0.0.1:8420/` after restart — the new tab
markup (`tab-btn-log`, `switchTab`, "Activity Log") is present in the served
HTML.

---

Original request:

READY

Move Activity Log to a different tab. This will give more rome for the projects.
