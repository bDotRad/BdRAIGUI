# Session scope & context — how to run Claude sessions on this fleet

Fleet-wide layer (see `Standards.md`). Companion to `BdRDev.md` (the
scheduler) and `Requests.md` (the request convention). Written
2026-08-29 after a run of requests (`rEcossystem 2`, `rEditing Tables`)
took six-plus passes each, mostly on re-orientation and question
round-trips rather than work.

## The model: context is working memory, rented by the turn

A session carries a "context" — the running transcript of everything it
has seen this run (files read, command output, messages). It is **text,
held only for that one run, never saved.** When the session ends it is
gone. What survives to the next session is only what was written to
disk: the repo, `CLAUDE.md`, `_Requests/_Archive/*`, the memory files.

- **Context too full** → every turn reprocesses the whole history:
  slow, token-hungry, quality drifts, and it eventually auto-compacts
  (which silently drops detail).
- **Context too empty** → the session doesn't know what it's doing and
  re-investigates things a previous session already worked out.

There is a sweet spot. You do **not** reach it by keeping more history —
you reach it by writing better notes to disk so a fresh start is a
well-informed start.

## Three ways a session can run

| Mode | Where | Upside | Failure mode |
|---|---|---|---|
| **Fresh per task** | this fleet's scheduler; `/clear` between tasks | cheap per turn, no bloat, no compaction | pays a relearn tax each start — size of the tax = quality of the handoff notes |
| **Persistent** | one never-cleared conversation (old VS Code habit) | never relearns | grows huge → slow + expensive → lossy compaction; drifts across unrelated tasks |
| **Persistent + interactive** | a human answering live (e.g. the Independent Claude tab) | fast: no round-trip delay on decisions | doesn't scale — cost piles up, and it's only fast *because* a human is in the loop |

The scheduler's fresh-per-request model is the right default. It was
slow in practice for two fixable reasons:

1. **One logical task was split across many requests**, so each session
   was effectively clearing *mid-task* and relearning every time.
2. **Archive writeups captured "what was done", not "what the next
   session needs to know."**

## Rules

- **The unit of work is one coherent task.** Start fresh → finish it →
  write down what matters → end. A task the session can't finish in one
  run (blocked on sudo, a decision, remote DDL) goes to `WAITING
  RESPONSE` per `Requests.md` — that's the handoff, make it complete.
- **Don't clear mid-task.** That's where relearning costs the most.
- **Don't run many unrelated tasks in one session.** That's the
  persistent-mode bloat.
- **Fix "too empty" with notes to disk, not more history.**

## Practices for this fleet

- **Scope each request so one session finishes it.** Split "make X
  work" into "draft the migration" / "write the app code" / "deploy
  checklist" — separate `READY` items, not one epic.
- **Front-load decisions.** A session that stops to ask a question then
  ends costs a full round-trip (hours to days). When dropping a
  request, pre-answer the obvious questions in the body.
- **Every archive writeup ends with two sections:**
  - *Non-obvious things learned about the code* — the conclusions that
    took cross-referencing to reach (e.g. "`apps` has no `project_id`",
    "SIGTERM won't restart the service, SIGKILL will").
  - *Still unknown / not verified* — so the next session knows where the
    edges are.
- **`CLAUDE.md`'s "Things that aren't obvious from the code" is the
  persistent-context channel.** Add to it whenever a session discovers
  something a cold reader of the code would miss.
