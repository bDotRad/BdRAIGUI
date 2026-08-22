# _Requests

Drop-box for bug reports / change requests / screenshots, for Claude Code
to process on request. Not part of the app itself -- just a working
folder between Brad and Claude.

This follows Brad's general "Claude Pi Workflow" request-intake
convention (not specific to BdRBirdDetector -- see `_Archived/260817_r004.md`
for the full doc as dropped here), adapted to how it's actually used in
this repo.

## How to add something

- A file or numbered folder, `rNNN.md` (or `rNNN/` if it needs supporting
  files alongside it -- screenshots, logs, etc.). Number doesn't need to
  be contiguous or sequential across files vs. folders, just unique.
- **First line of `rNNN.md` must be exactly `READY` or `NOT READY`**,
  nothing else on that line. That first line is the *only* thing that
  gates the whole file -- `READY`/`NOT READY`-looking text anywhere
  else in the body is just prose, not a marker, and doesn't get parsed
  as one. If a document genuinely covers multiple things with different
  readiness (e.g. "part A is decided, part B is still a draft"), split
  it into separate files (`r003a.md`, `r003b.md`) rather than marking
  a section mid-document -- there's no per-section marker syntax, and
  there isn't going to be one; simpler to just use separate files.
  Only `READY` requests get processed on a passive "scan requests" --
  drop a request in as `NOT READY` and flip it once it's actually
  ready. Naming a specific one directly ("scan r003") processes it
  regardless of its marker (or a missing/malformed one) -- an explicit
  ask from Brad is its own trigger.
- Prefix a file/folder name with `x` (e.g. `xr005.md`) to make Claude
  ignore it entirely, without deleting it.
- No required format for the body, but `Issue / When / Solution` (what's
  wrong, when it happens, any workaround already found) is a good
  default for bug reports.

## How to trigger processing

- **"scan requests"** -- process every `READY` item directly in
  `_Requests/` (not `_Archived/`).
- **"scan r004"** (or "scan 004", "scan 4") -- process just that one,
  regardless of what else is sitting in the folder.

## What happens after

Once a request's been read and either fixed or otherwise resolved:

1. Drop a summary `.md` in `_Archived/`, named `YYMMDD_r<NNN>[_r<NNN>...].md`
   (date processed + every request number it covers -- e.g.
   `260817_r001.md`, or `260817_r001_r002.md` if a couple were handled
   together in one pass). Content: what each numbered request asked for,
   what was found/done, and the outcome (fixed and deployed / investigated,
   no code change needed / etc).
2. Move the request's own file(s)/folder into `_Archived/` too, so
   `_Requests/` only shows what's still outstanding.

## Not yet built (per the convention doc, deferred until needed)

- Automated folder watcher -- purely manual/on-request for now.
- Sentinel-file READY marker instead of a first-line check.
- Email/SMS intake, or a small web UI once volume outgrows a visual scan.
