## What was done

**Investigated:** why the version string shown in the header (e.g.
`260826_205101 da1ecfe`, as pasted into the request) wasn't changing.

**Finding:** this is intentional, not a bug. `app_version()` in
`app/common.py` computes the version from the *running* code's current git
commit (`git log -1 --format=%cd %h`), and the docstring is explicit about
why it's cached:

> Since Flask runs with no autoreload, this is stable for the life of the
> process -- computed once and cached.

The dashboard process (`bdrdev-dashboard`) doesn't restart itself when new
commits land -- per this project's own CLAUDE.md, nothing here has
passwordless sudo, and `debug=False` means no autoreload either. So the
version badge is deliberately showing "what code this running process
actually is," not "what's the latest commit in the repo" -- those are
different things whenever a commit has landed since the last restart, which
is the normal state while a batch of requests is being processed. It only
advances at the next restart (Brad's `sudo systemctl restart
bdrdev-dashboard`, or a deliberate `kill -9` on the running PID, both
described in this project's CLAUDE.md).

Concretely: several commits landed this session
(`da1ecfe`, plus the Admin-panel-width fix from the paired request in this
same batch) after the version shown in the request was captured. The
dashboard has since been restarted again as part of verifying that other
work, so the version will already read past `da1ecfe` by the time this is
read.

**No code change made** -- behavior is correct as designed. If a
live-updating "latest repo commit" display (independent of what's actually
running) is wanted instead, that'd be a different, new feature -- happy to
build it, but didn't want to guess and build the wrong thing on top of a
one-line "why" question.

## Original request (verbatim)

READY

WHy isnt the version updating?
260826_205101 da1ecfe
