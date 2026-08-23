# 260822 — Browse archived requests, sorted by timestamp

## Done

Added an "Archive" button on each project card (`app/templates/index.html`)
that opens a modal browser over that project's `_Requests/_Archive/`
folder:

- `common.list_archive(project, subpath)` (`app/common.py`) lists one
  folder level, newest-first. Since the archiver prefixes filenames with
  `YYMMDD_`, a reverse alphabetical name sort doubles as a reverse-
  chronological sort, without needing to stat every file for mtime —
  which was the "sorted by timestamp...so it can be by name as the
  archiver adds the date to the front" idea from the request.
- `common.read_archive_file(project, rel_path)` reads a file for the
  viewer, restricted (via `Path.relative_to`) to stay inside the
  project's archive dir; non-text file types (images etc.) are reported
  as non-text rather than dumped as bytes.
- New routes `GET /api/archive/<project>` and
  `GET /api/archive/<project>/file` in `app/dashboard.py`.
- Modal UI supports drilling into subfolders (e.g. `rf Logo Sq/`) with
  breadcrumbs, and viewing a file's contents in a read-only textarea.

Verified via Flask test client: listing returns entries newest-first by
name, folder drill-down and file read both work, and path-escape attempts
(`../`) are rejected by the `relative_to` check.

## Requested

READY

can you add a way to see the archived files. a list that is sorted by timestamp...so it can be by name as the archiver adds the date to the front.
