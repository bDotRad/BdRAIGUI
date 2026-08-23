## What was asked

Brad clicked "Mark Ready" on a request card under an inactive project
and, on opening the actual file afterward, found its first line wasn't
`READY` — so how was the dashboard treating/setting it as ready?

## What was found

The activity log pinned it exactly:

```
2026-08-22T18:46:06Z  project=BdRBirdDetector  event=request_marked_ready  detail=README.md
```

`BdRBirdDetector/_Requests/README.md` is that project's own copy of the
request-intake convention doc (analogous to this repo's
`_Instructions/Requests.md`) — reference material, not a request. It
lives directly in `_Requests/` rather than under `_Archive(d)/`, and it
doesn't follow the `r<Title>` naming convention.

The bug: `common.scan_requests()` / `common.list_requests()` treated
*every* item directly under `_Requests/` as a request candidate, unless
it started with `_`, `.`, `x`, or `X`. README.md matched none of those,
so it showed up in the dashboard's per-project request list with a
"Not Ready" badge and a "Mark Ready" button, exactly like a real
request. Brad's click called `set_request_ready()`, which unconditionally
overwrites an item's first line with `READY` — so it did exactly what a
real request's marker flip does, just on the wrong kind of file. The
doc's original first line (almost certainly a `# _Requests`-style
heading, judging by the matching prose in this repo's own copy) got
clobbered by the literal string `READY`.

So the dashboard genuinely *was* setting it READY — the confusion was
that it never should have been offering that control on this file at
all.

## What changed

- `app/common.py`: added `_is_request_entry()` (checked against a new
  `_RESERVED_REQUEST_NAMES` set covering `README`/`README.md`/`README.txt`,
  case-insensitive) and switched `scan_requests()`, `list_requests()`,
  and `_resolve_request_target()` to use it instead of the bare
  `startswith(("_", ".", "x", "X"))` check. README-style reference docs
  dropped directly in `_Requests/` (this repo's own convention explicitly
  expects other projects to keep one) no longer count as requests, show
  in the request list, or can be targeted by the ready-toggle API —
  even by a direct/crafted call, not just the UI.
- `BdRBirdDetector/_Requests/README.md`: restored the clobbered first
  line to `# _Requests`, matching the heading style of this repo's own
  `_Instructions/Requests.md`, which the rest of that file's prose
  closely mirrors. This is an inferred restoration, not a recovered
  original (that repo's `_Requests/` is untracked in git, so there's no
  history to diff against) — worth a glance from Brad to confirm the
  heading text reads right.

## Outstanding — needs Brad

Both `bdraigui-dashboard` and `bdraigui-scheduler` run on the old
`common.py` until restarted (Flask has no autoreload, and this session
has no sudo). Please run when convenient:

```
sudo systemctl restart bdraigui-dashboard
sudo systemctl restart bdraigui-scheduler
```

Not urgent — `BdRBirdDetector` isn't currently in the rotation pool
(`state/selected_projects.json` only has `_BdRAIGUI`), so the stale
scheduler can't act on the mis-scanned README in the meantime. Left
both processes running rather than SIGKILLing them, since the scheduler
is the process managing *this* session.

---

Original request:

READY

I clicked ready on a file in another inactive project. when i opened that file it didnt have READY as the first line. how is it setting it as ready?
