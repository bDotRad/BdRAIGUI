WAITING RESPONSE

## Done — needs a dashboard restart to see it live (Claude, 2026-08-28)

**Documented** (fleet-wide, as asked): new
`_Instructions/WebUI.md` — the Edit / Save / Cancel table pattern
written normatively for ALL apps, plus versioning (7-char SHA) and a
look-&-feel baseline. Tied into the new two-layer doc system (see the
`rDocumentationrequirements` request) so every project inherits it.

**Implemented** on the **Ecosystem 2** grid
(`app/templates/index.html`):
- table is **read-only on load** — a single **Edit** button below it
- **Edit** → cells become editable, button row switches to **Save** +
  **Cancel**, edit hint appears
- **Save** → persists (Supabase or JSON fallback, unchanged), returns to
  read-only
- **Cancel** → discards edits (re-render from loaded data), returns to
  read-only
- derived columns (Other, Apps) stay non-editable in both modes

`kill -9` on the live dashboard is auto-mode-blocked for me, and there's
no autoreload, so **you need to run:**

```
sudo systemctl restart bdrdev-dashboard
```

then open the **Ecosystem 2** tab and check Edit / Save / Cancel.
Committed + pushed. Flip to `READY` with notes if the interaction isn't
what you meant, else archive.

---

The standard for editing tables is to have an edit button which changes from read only to editing.

Then a save and cancel button appears when in edit mode.

Save to save, cancel to cancel.

Can you update the Eco2 Table and also update the documentation to capture this requirements going forwards to ALL apps.
