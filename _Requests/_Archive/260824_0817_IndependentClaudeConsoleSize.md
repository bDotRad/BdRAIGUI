## What was done

Brad reported the "Independent Claude" console window (the console modal
opened via the new "Independent Claude" tab, `openConsole(INDEPENDENT_SESSION)`)
was too small — recent commands/output were getting hidden and needed
scrolling to see.

`app/templates/index.html` console modal CSS enlarged:
- `#console-modal`: `max-width` 760px → 1100px, `max-height` 85vh → 92vh
- `#console-pane`: `min-height` 320px → 600px

This is the same modal used for per-project consoles too, so all console
popups (not just Independent Claude) get the bigger window. The existing
auto-scroll-to-bottom behavior in `refreshConsole()` (sticks to bottom on
each poll if the user hadn't scrolled up) was left as-is — it already
does the right thing, it just had very little room to work with before.

**Not yet live / needs a restart:** Flask caches templates (`debug=False`,
no autoreload per this project's own CLAUDE.md), so this won't take
effect on the running dashboard until the process restarts. There's no
sudo in this session, so the only self-service restart path is `kill -9`
on the live `dashboard.py` process, which causes a brief outage — the
Claude Code auto-mode classifier blocked doing that without confirmation,
and Brad opted to do the `kill -9`/restart himself rather than have it
done automatically. **Action needed:** restart `bdraigui-dashboard`
(`sudo systemctl restart bdraigui-dashboard`, or `kill -9 <pid>` of the
`dashboard.py` process) to pick up the change, then verify.

Only `app/templates/index.html` was touched/committed here. Note:
`app/common.py`, `app/dashboard.py`, and `app/scheduler.py` already had
unrelated uncommitted changes sitting in the working tree before this
request (pre-existing WIP, not part of this fix) — left untouched.

---

READY

Window needs to be bigger and scoll up if possible. commands were hidden
