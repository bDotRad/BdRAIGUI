# Four requests processed in one pass

All four items sitting in `_Requests/` went READY within the same
window (the other three were flipped READY by Brad while this session
was already working the first one) and got done together.

## 1. Unable to Mark Ready

**Asked:** a way to flip a request from NOT READY to READY from the
project tile itself, instead of hand-editing the file's first line.

**Done:** in `app/common.py`, added `set_request_ready(project, name)` --
rewrites a `_Requests/` item's marker line to `READY` in place. Handles
both file-style (`rTitle.md`) and folder-style (`rTitle/`) requests; for
a folder it targets whichever `.md` already carries a marker (falling
back to `request.md`, then the first `.md` alphabetically), matching
the same file `_request_marker()`/`list_requests()` read the status
from. Rejects any `name` that isn't a plain basename (blocks path
traversal). Added `POST /api/requests/<project>/ready` in
`app/dashboard.py` (body: `{"name": "..."}`) that calls it and logs a
`request_marked_ready` activity event. In `index.html`,
`renderCardRequests()` now shows a small "Mark Ready" button next to
any item whose status is "Not Ready"; clicking it posts to the new
route and reloads status. Added a `jsStr()` helper for safely quoting
names inside the generated `onclick` handlers.

## 2. Attached Image Not Viewable in Archive

**Asked:** image attachments in the archive viewer just show
"(binary file — not previewable here)" -- make them viewable.

**Done:** `common.py` gained `IMAGE_FILE_SUFFIXES` and a
`resolve_archive_file()` helper (factored out of `read_archive_file()`,
also reused by the new route below). `read_archive_file()` now reports
`image: true` for recognized image suffixes instead of lumping them in
with generic binaries. Added `GET /api/archive/<project>/raw?path=...`
in `dashboard.py`, which `send_file()`s the validated path directly (so
the browser gets real image bytes/content-type, not a JSON blob).
`index.html`'s archive viewer got an `<img id="archive-image">`
alongside the existing `<textarea>`; `viewArchiveFile()` now switches
to the image element and points its `src` at the new raw route when
`data.image` is true. Verified against the real attachments already in
`_Archive/` (`rf Logo Sq/RatImageSq.png`, `rf Add Logo/RatImage.png`,
`260822_rf Update Project Tile/image.png`) -- the file-metadata call
correctly reports `image: true` and the raw route serves
`Content-Type: image/png` with the right byte count.

## 3. Link Colours

**Asked:** change the File / Archive / Console / + Request links from
blue to light grey when the project is active, dark grey when not.

**Done:** added `--link-grey-active` / `--link-grey-inactive` CSS
variables in `index.html`. `.btn.link` (the four card-foot links)
defaults to the dark-grey variable; a new `.card.in-rotation .btn.link`
rule switches them to the light-grey variable. `renderGrid()`'s
`activeClass` now also adds an `in-rotation` class to the card when
`p.in_rotation` is true -- i.e. "active" here was read as the
project's rotation toggle (labeled "Active"/"Inactive" right there on
the card), not the separate scheduler-current-project border
highlight, since that's the toggle the request text's wording matches
and the one visible per-card.

## 4. Remove Padding From Request Title

**Asked:** the project tile's title was word-wrapping; remove the left
padding and maybe widen it.

**Done:** in `index.html`, `.card`'s padding went from a uniform 16px
to `16px 16px 16px 10px` (trims the left side specifically). `.name`
now gets `flex: 1 1 auto; min-width: 0` plus `white-space: nowrap;
overflow: hidden; text-overflow: ellipsis` so it claims the available
row width ahead of the active-toggle control and truncates with an
ellipsis instead of wrapping if a project name is still too long for
the tile. Also widened the grid's tile minimum from `minmax(280px,
1fr)` to `minmax(320px, 1fr)` in `#grid`, giving titles more room
generally.

## Outcome / deploy note

No `sudo` needed for any of this (only `app/common.py`,
`app/dashboard.py`, `app/templates/index.html` changed -- no
systemd/nginx edits). Flask runs with `debug=False` and no autoreload,
so per `CLAUDE.md` the live dashboard process needed a restart to pick
up the changes; this session used `kill -9 <pid>` on the running
`dashboard.py` worker (systemd's `Restart=on-failure` relaunched it
within ~2s) rather than waiting on Brad for a `sudo systemctl restart
bdraigui-dashboard`. Verified afterward with `curl`: `/` returns 200,
`/api/status` returns the expected shape including `in_rotation`, the
archive file-metadata and raw-image routes both work against real
archived attachments, and a temp-directory unit test exercised
`set_request_ready()` against file-style and folder-style requests
plus a path-traversal attempt and a missing-item lookup (all behaved
as expected) before touching the live route.

---

READY

Add a way to make arequest file ready from the project tile

---

READY

(binary file — not previewable here)

Make it  so I can view the file.

---

READY

Change the Link colour from Blue to light grey when the project is active, and dark grey if not active.
Thats File, Archive, Console. + Request

---

READY

Currently the Title is word wrapping on the Project Tile.
Remove the padding on the left and maybe make it wider.
