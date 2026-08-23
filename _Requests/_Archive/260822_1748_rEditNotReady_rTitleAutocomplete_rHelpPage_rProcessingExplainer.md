# Four requests processed in one pass

All four items landed in `_Requests/` while this session was already
working the first one (same pattern as
[[260822_1729_rMarkReady_rArchiveImage_rLinkColours_rTitleWrap]]) and got
done together.

## 1. Edit NOT READY requests from the dashboard

**Asked:** "Add the ability to edit the files NOT READY."

**Done:** a request marked **Not Ready** on a project card now has an
**Edit** button next to **Mark Ready** ([[260822_1729_rMarkReady_rArchiveImage_rLinkColours_rTitleWrap]]'s
feature). Clicking it opens a small modal with the request's body text
in a textarea; **Save** writes it back without touching the marker line.

- `app/common.py`: factored the target-resolution logic out of
  `set_request_ready()` into `_resolve_request_target(project, name)`
  (same file-or-folder rules as before -- for a folder, whichever `.md`
  carries a marker, falling back to `request.md`, then the first `.md`
  alphabetically). Added `read_request_body()` (everything after the
  marker line) and `write_request_body()` (rewrites the body, keeps
  whatever marker was already there).
- `app/dashboard.py`: `GET /api/requests/<project>/content?name=...` and
  `POST /api/requests/<project>/content` (body: `{"name", "content"}`).
- `app/templates/index.html`: new `#edit-req-overlay`/`#edit-req-modal`
  (styled to match the existing `+ Request` modal), `openEditRequest()` /
  `saveEditRequest()` / `closeEditRequest()`, and an `Edit` button in
  `renderCardRequests()` alongside `Mark Ready`.

**Outcome:** verified via Flask's test client -- content GET/POST
round-trip preserves the marker line, a missing/path-traversal `name`
404s, and folder-style requests (`.md` inside a subfolder) resolve the
same target file `Mark Ready` already used. Needs a dashboard restart to
go live (see restart note below).

## 2. Title box showing old-entry autocomplete suggestions

**Asked:** "When I click in the Title Box it has a heap of suggestions
from previous entries."

**Found:** `#req-title-input` (the `+ Request` modal's title field) had
no `autocomplete` attribute, so Chrome/Firefox were offering browser
autofill suggestions built from every title ever typed into that field.

**Done:** added `autocomplete="off"` to `#req-title-input` in
`app/templates/index.html`.

## 3. Help page

**Asked:** "Make a Help Page that explains the different statuses etc.
very basic, but just shows all the options."

**Done:** new `app/templates/help.html`, served at `GET /help`, linked
from a small "Help" link on the main dashboard's tab bar
(`app/templates/index.html`). Plain reference page (no JS/API calls) —
explains the four request statuses (Not Ready / Ready / Processing /
Waiting Response) and the project-card controls (Active/Inactive,
Files, Archive, Console, + Request), reusing the same pill styling as
the status badges elsewhere in the app.

## 4. "Is Processing actually processing all of them?"

**Asked:** "If I have 3 requests ready, all go to processing. Is it
processing all three? or does it just put the request into that status
when it should be waiting."

**Answer:** Not a bug -- confirmed against `app/scheduler.py`'s
`main_loop()`: the scheduler tracks phase per *project*, not per
request. Once a project has any Ready requests, it wakes (or nudges) one
Claude Code session for that project and sets phase to `processing` for
the whole pass; `list_requests()` (`app/common.py`) then shows every
Ready item in that project as "Processing" for as long as that phase
holds, not just the one currently being edited. The session actually
works through them one at a time, sequentially, in the same pass -- this
exact session did that just now (this request was one of three
processed alongside it). So "Processing" means "in this session's
current queue," not "being edited this literal instant." Folded this
explanation into the new Help page (item 3 above) rather than leaving it
only in this archive entry, so it's visible in-app going forward.

**Outcome:** no code change needed for this one -- answered + documented.

---

## Restart note

All of today's earlier template/asset changes were already sitting
uncommitted on disk before this pass touched anything further (see
`git diff --stat` from earlier in the day) -- `app/common.py`,
`app/dashboard.py`, `app/scheduler.py`, `app/static/rat-logo.png`,
`app/templates/index.html`, plus the new `app/templates/project.html`.
This pass adds `app/templates/help.html` on top of that. Flask runs with
`debug=False`/no autoreload, so none of it — old or new — is live yet.
No passwordless sudo here, so the restart itself is Brad's to run:

    sudo systemctl restart bdraigui-dashboard

(or, if it's still running as a bare process rather than under systemd,
`kill -9 <pid>` on the current `dashboard.py` process is enough to pick
up the change — SIGKILL counts as a failure under
`Restart=on-failure`/gets systemd to relaunch it, or just needs a manual
relaunch if it's not under systemd yet.)

---

## Original requests (verbatim)

### rFiles Not Ready.md
```
READY

Add the ability to edit the files NOT READY
```

### rTitle Box Suggestions.md
```
READY

When I click in the Title Box it has a heap of suggestions from previous entries.
```

### rHelp Page.md
```
READY

Make a Help Page that explains the differnt statuses etc. very basic, but just shows all the options.
```

### rProcessing Status.md
```
READY

If I have 3 requests ready, all go to processing. Is it processing all three? or does it just put the request into that status when it should be waiting.
```
