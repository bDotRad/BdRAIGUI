# 260822 — Logo overlapping the status bar

## Done

Found `#site-logo` in `app/templates/index.html` sized 100x100 (from the
prior `rLogoSq` request), fixed at `top:16px; left:16px`. At that size it
reached down to y=116px, overlapping the `#banner` status/phase bar that
sits just below the title and subtitle.

Shrunk `#site-logo` to 48x48 (ends at y=64px, well clear of the banner),
and reduced `h1`/`.subtitle` `margin-left` from 116px to 64px to match.
Marked "for now" per the request — a from-scratch relayout (e.g. logo
inline in a header row instead of `position: fixed`) would be a more
durable fix if the banner or title text grows.

Verified via Flask test client that `/` renders with `width: 48px` on
`#site-logo`. Live dashboard needs a restart to pick this up (see
outstanding restart note below).

## Requested

READY

logo is overlapping the status bar. make it smaller for now
