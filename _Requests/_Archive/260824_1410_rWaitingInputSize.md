## What was asked

Make the Waiting Input popup bigger vertically -- double the size, or make
it resizable.

## What changed

`app/templates/index.html`, `#waiting-modal` CSS:
- Was `max-height: 85vh` with height driven by content (so it rendered
  small whenever the list/edit pane didn't need much room).
- Now fixed at `height: 90vh` (with `min-height: 320px` as a floor), so it
  reliably fills most of the viewport instead of shrinking to fit content.
- Added `resize: vertical; overflow: auto;` so Brad can also drag the
  modal's bottom edge to resize it further by hand if 90vh isn't enough on
  a given screen.

## Outcome

Fixed and deployed -- restarted the live dashboard via its own
`/api/admin/restart` self-restart endpoint (no `sudo`/manual restart
needed from Brad) and confirmed via `curl` that the new CSS is live.

---

## Original request

READY

Make the popup bigger vertically double size or make resizable
