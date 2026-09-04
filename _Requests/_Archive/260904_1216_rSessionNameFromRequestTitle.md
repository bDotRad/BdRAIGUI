# Scheduler: name each session after the request it's processing

**Processed:** 2026-09-04 12:16 — unattended pass.
**Outcome:** Done in code, committed + pushed. **Needs a scheduler restart**
to take effect (Brad, or next natural restart) — see below.

## What was asked

Every scheduler-spawned session shows up as "Check the requests folder…"
in CloudCLI's sidebar and `claude --resume`, because the naming surfaces
use the first few words of the first user message and the scheduler
always sent one fixed string (`SCAN_PROMPT`). Make the wake prompt lead
with the READY request title(s) so the name means something.

## What changed

`app/scheduler.py`:

- `SCAN_PROMPT` (module constant) split into:
  - `SCAN_PROMPT_TAIL` — the unattended-behaviour half, **verbatim**
    (cancel interactive prompts, write questions into the request file,
    flip to `WAITING RESPONSE`, end turn, see `_Instructions/BdRDev.md`).
  - `SCAN_PROMPT_GENERIC_HEAD` — the old "Check the requests folder…"
    opener, now only the fallback.
  - `build_scan_prompt(project)` — reads the project's outstanding items
    via `common.list_requests(project)`, keeps the ones showing as
    `Ready` / `Processing`, and builds
    `Process these pending requests now: "Title A", "Title B". ` + tail.
    Zero titles (race / edge case) → generic head instead of an empty
    list. Any exception from `list_requests` → generic head.
- `send_prompt(project)` now calls `build_scan_prompt(project)` instead
  of the constant. This is the single send path — it covers **both** the
  initial nudge (`spawn_session` → `send_prompt`) and the mid-session
  re-prompt when more items appear (`main_loop`, the
  `just_spawned or pending > tracked["prompted"]` branch).

Behaviour notes from the ask, all honoured:

- A session is named only for what was pending at the **first** prompt;
  later items picked up in the same session don't rename it. Acceptable.
- `WAITING RESPONSE` items are excluded (they don't trigger a wake and
  aren't what the session is working on).

## Testing

No test suite in this repo. Verified in isolation (per the ask — a broken
scheduler can't restart itself, so no live-restart smoke test):

```
cd app && python3 -c "import ast; ast.parse(open('scheduler.py').read())"   # syntax OK
cd app && python3 -c "import scheduler; print(scheduler.build_scan_prompt('BdRDev'))"
  -> Process these pending requests now: "Session name from request title". This session runs unattended -- …
cd app && python3 -c "import scheduler; print(scheduler.build_scan_prompt('NoSuchProject'))"
  -> Check the requests folder for new or updated files and process them now. This session runs unattended -- …
```

## Left for Brad

The running `bdrdev-scheduler` systemd service won't pick this up until
restarted. No sudo here, and SIGKILL of the scheduler is not a casual
unattended move (it manages its own wake/sleep). Not urgent — it's a
cosmetic prompt change with no state-file or dashboard impact.

```
"Pick up the build_scan_prompt change in app/scheduler.py"
sudo systemctl restart bdrdev-scheduler
```

---

## Original request (verbatim)

READY

# Scheduler: name each session after the request it's processing

## Problem

Every scheduler-spawned session shows up as "Check the requests folder…"
in CloudCLI's sidebar and `claude --resume`. That name is derived from
the first user message, and the scheduler always sends the same fixed
prompt (`SCAN_PROMPT`, `app/scheduler.py:58`), which starts
"Check the requests folder for new or updated files…". Claude Code never
writes its own summary for these unattended sessions, and there's no
supported way to rename a session after it's created — so it has to be
steered at spawn time.

## Ask

Make the wake prompt lead with the READY request title(s) so the
first few words — which is all the naming surfaces use — become
meaningful.

- Turn `SCAN_PROMPT` (a module constant) into a small function that
  takes the project name, reads its READY items via
  `common.list_requests(project)` (each entry has a `title`), and builds
  a prompt that opens with them, e.g.:

  > `Process these pending requests now: "Ecosystem web-access columns". This session runs unattended -- nobody is watching the terminal. If you hit a decision only Brad can make…` *(rest unchanged)*

- Keep the existing unattended-behaviour instructions verbatim (cancel
  interactive prompts, write questions into the request file, set it to
  `WAITING RESPONSE`, end turn — see `_Instructions/BdRDev.md`).
- Apply it in both places the prompt is sent: the initial nudge and the
  re-prompt path when new requests appear mid-session
  (`app/scheduler.py:250`).
- If zero titles resolve (edge case / race), fall back to the current
  generic wording rather than sending an empty list.

## Notes / caveats

- A session handles whatever goes READY over its whole lifetime, so the
  name only reflects what was pending at the **first** prompt — later
  requests picked up in the same session won't rename it. That's
  acceptable; still far better than every session reading identically.
- `app/scheduler.py` is the thing that manages this project's own
  wake/sleep cycle — test the prompt-building in isolation, and don't
  rely on a live restart to catch a syntax error. A broken scheduler
  can't restart itself.
- Pure prompt-text change; no state-file or dashboard impact.
