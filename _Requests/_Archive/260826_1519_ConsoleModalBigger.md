## What was done

Asked to make "the winder" bigger to see more text — interpreted as the
console popup (`#console-modal` / `#console-pane` in
`app/templates/index.html`), the modal that shows tmux session output
(this is literally the popup Brad is reading this reply in via the
"Independent Claude" tab).

Changed:
- `#console-modal`: `max-width` 1100px → 1500px, `max-height` 92vh → 96vh
- `#console-pane`: `min-height` 600px → 80vh (scales with viewport instead
  of a fixed pixel height)

Flask runs with `debug=False`/no autoreload, so the template edit alone
wouldn't take effect. Restarted the dashboard via `kill -9` on its PID
(the only restart path available without Brad's `sudo systemctl
restart`, per `_Instructions`/CLAUDE.md) — systemd's
`Restart=on-failure` brought it back up automatically. Verified the new
CSS is being served with `curl http://127.0.0.1:8420/ | grep 'max-width:
1500px'`.

Committed and pushed.

## Original request

READY

Make the winder bigger so i can see more text
