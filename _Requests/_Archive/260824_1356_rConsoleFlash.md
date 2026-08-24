## What was asked

Console button flashes in a project card (PlanBdRad, spelled "PlanBdotRad" in
the request) when a request goes to `WAITING RESPONSE`. Opening Console shows
nothing, because the Claude session that set that marker has already exited
and the tmux pane it was peeking at is gone. Ask: add a place, like the
existing Archive button/modal, to see Waiting Response requests, edit the
file, and set it back to READY.

## What was found

The flashing wasn't actually wrong -- `WAITING RESPONSE` genuinely means
"needs a human" -- but it pointed at the wrong action. Console peeks at a
live tmux session; once that session exits (which it does right after
writing `WAITING RESPONSE`), there's nothing left to peek at.

Worse, there was no way to actually resolve a Waiting Response request from
the dashboard at all:
- The per-card mini request list (`app/templates/index.html`,
  `renderCardRequests`) only showed a "Mark Ready" button for `Not Ready`
  items and "Mark Not Ready" for `Ready`/`Processing` -- nothing for
  `Waiting Response`.
- The existing "Edit request" modal (`openEditRequest`/`saveEditRequest`)
  can edit a request's body, but has no way to flip its marker line back to
  `READY` -- it calls `/api/requests/<project>/content`, which by design
  (`common.write_request_body`) preserves whatever marker is already on
  disk.
- `/project/<project>`'s Requests panel has the same gap (Shelve only, no
  ready/not-ready toggle of any kind).

So a genuine Waiting Response request had no UI path to resolution --
Brad's only option was editing the file directly on disk.

## What changed

Added a new "Waiting Input" button to each project card in
`app/templates/index.html`, next to Archive/Console (visible always, same
as those). It replaces Console as the thing that flashes when the project
has a `Waiting Response` item (Console no longer flashes, since it isn't
the useful destination anymore).

Clicking it opens a new modal styled like the Archive modal (list on the
left, detail pane on the right): the left list shows just this project's
`Waiting Response` requests; picking one shows the question/context and an
editable textarea of the current body, plus **Save** and **Save & Mark
Ready** buttons. Save & Mark Ready calls the existing
`/api/requests/<project>/content` (save the edited body) then
`/api/requests/<project>/ready` (flip the marker to `READY`) -- both
endpoints already existed and needed no backend changes.

Also added a "Waiting Input" entry to the help page
(`app/templates/help.html`) describing the new button.

Verified against the live project data (a real `Waiting Response` request
already sitting in `PlanBdRad/_Requests/rInitial Setup.md`) on an isolated
test port before touching the live service, then restarted the live
dashboard (self-restart endpoint, `kill -9` + systemd relaunch -- brief
outage) and confirmed via `curl` that the new button/modal and help text
are live and the real Waiting Response request shows up correctly through
the new endpoint calls.

## Outcome

Fixed and deployed -- live dashboard restarted and verified via curl. No
`sudo`/manual restart needed from Brad this time (used the dashboard's own
self-restart admin endpoint).

---

## Original request

READY

The console is flashing in PlanBdotRad
When i Open the console the console is empty because the claude session is closed and the files updated.
Need to add a folder/tab for Waiting Input
Then i can open taht similar to the Archive Tab, and edit the file to the right and then set to READY.
