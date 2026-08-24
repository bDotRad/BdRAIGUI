# rTaking Forever — why does the scan-requests pass take so long

**Asked:** "Why is the claude command rescan files taking forever"

**Found:** Checked `state/activity_log.jsonl` and `state/scheduler_state.json`
against wall-clock time for this exact request:

- `09:46:32` — request created (`rTaking Forever.md` dropped into
  `_Requests/`).
- `09:46:36` — scheduler's next poll tick (`POLL_TICK_SECONDS = 5`) saw
  it, logged `requests_ready`, and since this project's session had
  hibernated, spawned a fresh one (`session_waking`) — 4 seconds after
  creation, not slow.
- From there it's genuine Claude Code think/tool-use time: a fresh
  session takes up to `SPAWN_READY_TIMEOUT = 20`s just to boot to an
  interactive prompt, then this pass in particular found a backlog of
  already-verified-but-never-committed code sitting in the working tree
  (the Independent Claude session + concurrent-scheduling work, plus
  three console-clipping fixes — see the new `6814a1b` commit) and spent
  several minutes confirming it was safe and committing/pushing it
  *before* even getting to this question.

So there's no stuck/hung state, no scheduler bug, and no queueing delay
for this request specifically — it's the sum of one real (if small)
fixed cost (session boot) plus however long the actual Claude turn takes
to do the work, which varies a lot request to request. A wake that lands
on a session with genuine backlog or a big diff to review will visibly
take longer than a one-line CSS tweak.

Two things worth knowing if this comes up again:
- The dashboard's console popup polls the live tmux pane every 3s
  (`consolePollTimer` in `index.html`), so watching that tab shows
  real-time progress instead of just a wait-then-final-reply.
- The scheduler now runs up to `MAX_CONCURRENT = 2` projects at once
  (see the same backlog commit). If more than 2 selected projects have
  pending work simultaneously, the extras queue for a free slot — worth
  checking `state/scheduler_state.json`'s `active_projects` if a
  *different* project's request seems to be sitting untouched, since
  that would show up there as not-yet-active rather than as a slow
  in-progress session.

**Outcome:** investigated, no code change needed — explained above.

---

READY

Why is the claude command rescan files taking forever
