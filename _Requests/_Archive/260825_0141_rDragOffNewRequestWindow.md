## What was done

**Issue:** Resizing the New Request modal's textarea and dragging the mouse
past the modal's bottom-right edge onto the page behind it caused the whole
popup to disappear, losing whatever had been typed.

**Root cause:** `#req-overlay`'s click handler
(`app/templates/index.html`) closed the modal whenever the click event's
`target` was the overlay backdrop itself:

```js
document.getElementById('req-overlay').addEventListener('click', (e) => {
  if (e.target.id === 'req-overlay') closeRequest();
});
```

This is meant to catch a genuine "click outside the modal to dismiss it."
But a native `<textarea>` resize-drag starts with `mousedown` on the
textarea and, if dragged far enough, ends with `mouseup` over the backdrop.
Per the DOM click spec, the browser fires `click` on the nearest common
ancestor of the `mousedown` and `mouseup` targets -- which is `#req-overlay`
itself, since it contains the modal which contains the textarea. So a
resize-drag that crossed the modal edge was indistinguishable from an
intentional click on the backdrop, and closed the modal mid-edit.

**Fix:** Track whether the `mousedown` that started the current click also
landed on the overlay itself. Only close on click if both the `mousedown`
*and* the `click` targeted the backdrop directly -- a drag that started
inside the modal (textarea resize handle included) no longer counts as an
outside click, even if the drag ends over the backdrop.

Changed `app/templates/index.html` (the `req-overlay` click-outside
handler, near the bottom of the script block). Verified the change is live
by force-restarting `bdraigui-dashboard` (`kill -9` on the old PID, per
this repo's no-sudo/no-autoreload convention -- `systemctl` confirmed
`active` afterward, and `curl localhost:8420/` shows the new
`reqOverlayMousedownOnSelf` guard in the served HTML) and confirming the
service came back up cleanly.

Scope note: the same click-outside pattern (and thus the same
theoretical bug) exists on the edit-request, SQL, waiting-input,
console, and archive overlays too, but this request only asked about the
New Request window, so only `#req-overlay` was touched.

**Outcome:** Fixed and deployed.

---

## Original request

READY

WHen I resize the New Request window, if i drag off the bottom right to the page below, the popup disappears and i lose everything. find a way not for that to happen.
