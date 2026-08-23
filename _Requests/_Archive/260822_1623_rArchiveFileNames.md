# 260822 — Archive filenames now carry HHMM, not just the date

## Done

**Why:** the archive browser (`common.list_archive`, added earlier today
in [[260822_1535_rArchiveBrowse]]) sorts newest-first by doing a reverse
alphabetical sort on filename, relying on the `YYMMDD_` prefix to double
as chronological order. That breaks down on any day with more than one
archived request, since same-day files then sort by slug instead of by
when they were actually written — which is every day so far, since the
whole convention is only a few hours old (see
[[260822_1537_rArchiveConvention]]).

**Fixed:**
- Renamed every `.md` file already in `_Requests/_Archive/` (this
  project's own archive) from `YYMMDD_<slug>.md` to
  `YYMMDD_HHMM_<slug>.md`, using each file's on-disk last-modified time
  as the "when it was archived" timestamp:
  - `260822_rGUIFiles.md` → `260822_1224_rGUIFiles.md`
  - `260822_rAddLogo.md` → `260822_1303_rAddLogo.md`
  - `260822_rUpdateInstructions.md` → `260822_1350_rUpdateInstructions.md`
  - `260822_r1_r2.md` → `260822_1408_r1_r2.md`
  - `260822_rLogoSq.md` → `260822_1421_rLogoSq.md`
  - `260822_rLogoOverlap.md` → `260822_1535_rLogoOverlap.md`
  - `260822_rArchiveBrowse.md` → `260822_1535_rArchiveBrowse.md`
  - `260822_rProjectPage.md` → `260822_1535_rProjectPage.md`
  - `260822_rArchiveConvention.md` → `260822_1537_rArchiveConvention.md`
  - `260822_rRequestTitleNaming.md` → `260822_1606_rRequestTitleNaming.md`
  - `260822_rMoveActivityLog.md` → `260822_1610_rMoveActivityLog.md`
  - `260822_rArchivePanelLayout.md` → `260822_1614_rArchivePanelLayout.md`
  - Fixed up the couple of `[[wikilink]]`-style and backtick
    cross-references between archive files that named the old filenames.
- Left the `rf GUI Files/`, `rf Add Logo/`, `rf Logo Sq/` attachment
  folders as-is (no date/time prefix) — that was a deliberate call made
  in [[260822_1537_rArchiveConvention]] since each already has a proper
  timestamped `.md` summary alongside it, and folder-renaming would have
  meant also rewriting the several summaries that reference them by name.
- Updated `_Instructions/Requests.md`'s archive-naming section to specify
  `YYMMDD_HHMM_<short-name>.md` going forward, with a note on why (same
  reasoning as above), and updated the matching docstring comment in
  `app/common.py` (`list_archive`).
- No code change needed in `list_archive` itself — the sort is a plain
  string comparison on the full filename, so it already produces correct
  ordering once the filenames themselves carry the time.

**Known edge case, accepted as-is:** the format is minute-granularity.
Three requests from this same archiving pass landed in the same minute
(`260822_1535_...`), so `rArchiveBrowse`/`rLogoOverlap`/`rProjectPage`
still just sort by slug relative to each other rather than true
processing order. Not worth going to second-granularity for.

## Requested

READY

Name the files yymmdd_hhmm title so that they order correctly.
can you rename everything in archive from the last saved time stamp
