# 260822 — Archiving convention: no summary for r3, r1/r2 reuse, new format

## Done

**Why there was no archive file for r3:** r3 (the per-project detail
page request) got implemented, but whoever/whatever processed it moved
the raw `r3.md` into `_Archive/` under its own name and stopped there --
no summary was ever written. That's just a dropped step, not an
intentional behavior. It's fixed now: `260822_1535_rProjectPage.md` in this
same archive folder is r3's proper write-up.

**Why r1 and r2 in `_Archive/` had different content than expected:**
the original r1 ("make the logo square and bigger") and r2 ("activity
log timestamp wrong") were combined and archived correctly as
`260822_1408_r1_r2.md` -- that part was fine. But because requests get
renumbered from 1 once their files leave `_Requests/`, two *new* and
unrelated requests -- "logo is overlapping the status bar, make it
smaller" and "add a way to see archived files sorted by timestamp" --
later landed as `r1.md`/`r2.md` again, and when *those* got archived the
old way (move-under-same-name), they silently overwrote the original
raw `r1.md`/`r2.md` already sitting in `_Archive/`. No data was actually
lost (the real record, `260822_1408_r1_r2.md`, was untouched), but it made
`_Archive/` confusing to read. Both of those newer requests are now
properly written up as `260822_1535_rLogoOverlap.md` and
`260822_1535_rArchiveBrowse.md`.

**Convention change**, per what was asked -- updated
`_Instructions/Requests.md`:
- Archived files are now named `YYMMDD_<short-name>.md` -- a
  descriptive slug, not the original `rNNN` -- specifically so this
  overwrite can't happen again (nothing in `_Archive/` is ever named
  after an inbox slot that can get reused).
- Each archived file is now self-contained: **top half is what was
  done, bottom half is the original request verbatim** -- no more
  separate raw-copy-plus-summary pair.
- Added a `WAITING RESPONSE` marker: if a request can't be finished
  (blocked on something only Brad can answer), it stays in `_Requests/`
  instead of moving to `_Archive/` half-done, with `WAITING RESPONSE` on
  line one and a note on what's blocking it.
- No code changes were needed for the marker itself -- `common._is_ready()`
  already treats anything other than exactly `READY` as not-ready, so
  `WAITING RESPONSE` behaves like `NOT READY` for scanning purposes
  without any change.

**Archive tidy-up:** removed the leftover bare `r1.md`, `r2.md`, `r3.md`
raw copies from `_Archive/` now that their content lives in the
timestamped write-ups above. Left the existing `rf ...` reference
folders (`rf GUI Files`, `rf Add Logo`, `rf Logo Sq`) as they were --
each already has a proper `YYMMDD_...` summary alongside it and holds
genuine attachments (images, source files) worth keeping.

## Requested

READY

how come there is no archive file for r3.

and there is also r1 and r2...it was combined which is ok.

when you archive, make the file
time stamp name.md

the top of the file is what was done, the bottom half is what was requested.

if the request couldnt be complete, leave it in the request folder and flag it.

put WAITING REPONSE on the first line.

can you update the instructions documentation to reflect this.

and do a tidy up of the archive folder
