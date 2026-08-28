WAITING RESPONSE

## Second pass (Claude, 2026-08-28 pm)

Your three follow-ups:

### 1. "Said saving to json not supabase, unreachable"

That message was misleading. **Supabase was never actually wired into
the running dashboard** — every `SUPABASE_*` line in
`systemd/bdrdev-dashboard.service` is commented out, and the installed
unit has none of them. So the editor has always used the
`state/ecosystem.json` fallback; it wasn't "unreachable", it was "not
configured".

Fixed the wording: `/api/ecosystem` now reports `supabase_configured`,
and the source line / save toast say **"Supabase not configured on this
box"** vs **"configured but unreachable"** as appropriate.

To make it actually save to Supabase, the dashboard service needs the
env vars. Good news — the Pi's PostgREST API **is** reachable from this
dev box over the LAN IP (`https://10.10.10.20/rest/v1/` → 401, i.e. it
answers). `bdrpiami.local` does *not* resolve from here, so the URL has
to be the IP, and TLS verification has to be off (the Pi's cert is for
`bdrpiami.local`). Action block below.

### 2. "I couldnt edit the APPs" (in Ecosystem 2)

The **Apps** column in the Ecosystem 2 grid is *derived* — it's built by
matching each app's `server` field to the server name. It's read-only
there by design (same as the "Other" column). Apps are managed on the
**Fleet** tab. Added a link in the Eco2 edit hint that jumps straight
there.

### 3. "Select the apps that are on that server, not type it in"

Done. On the **Fleet** tab, each app's **"Runs on server"** field is now
a **dropdown of the defined servers** instead of a free-text box. Pick
the server; the Ecosystem 2 "Apps" column updates to match on save. (Any
existing free-text value that isn't a known server name is kept as an
extra option so nothing is lost.)

Note on "There is an APPs table with description": the Fleet tab's app
rows already have Name / Runs on server / Tag / Web address / DB /
Planned. There's no separate free-text "description" field on an app
today — if you want one, say so and I'll add it (plus a column for it).

All committed + pushed (`2694755`). Needs a dashboard restart.

@@@ --- Action --- @@@

1. Restart the dashboard to load the new template + routes (also picks
   up the Processing tab from `rAdd Check Proc Status`).

"Click Admin -> System -> 'Restart service', or on this dev box:"
sudo systemctl restart bdrdev-dashboard

"Then: Fleet tab -> an app -> 'Runs on server' is now a dropdown.
 Ecosystem 2 tab -> Edit / Save / Cancel."

2. (Optional — only if you answer 2 to the question below.) Wire the
   dashboard service to the Pi's Supabase. You'll need the service-role
   JWT from the Pi: `~/projects/BdRPiAMI/SECRETS.md` on bdrpiami (the
   service_role / SERVICE_KEY value).

"Open the dashboard unit for editing"                       # on this dev box
sudo systemctl edit --full bdrdev-dashboard

"Uncomment and set these three lines in the [Service] section
 (paste the real JWT for the key):"
    Environment=SUPABASE_URL=https://10.10.10.20
    Environment=SUPABASE_SERVICE_KEY=<paste the service_role JWT>
    Environment=SUPABASE_VERIFY_SSL=0

"Reload systemd and restart the dashboard"                  # on this dev box
sudo systemctl daemon-reload
sudo systemctl restart bdrdev-dashboard

"Confirm the API answers from here (expect 401, meaning reachable)"
curl -s -o /dev/null -w '%{http_code}\n' -k https://10.10.10.20/rest/v1/

@@@ ------------- @@@

??? --- Question --- ???

Do you want the fleet data actually stored in Supabase now, or is the
local JSON file fine for the moment?

Options:
1. JSON is fine for now (recommended) — the editor works, the data isn't
   critical, and Supabase wiring can wait until the Pi is renamed and
   has a cert that matches. Do Action step 1 only; skip step 2. Archive
   this once the dropdown + Edit/Save/Cancel check out.
2. Wire up Supabase now — do Action step 2 as well. Flip back to READY
   with a note if the source line doesn't switch to "source: Supabase".

Answer:


??? --------------- ???

---

Didnt quite work. Said saving to json not supabase, unreachable.

ALso i couldnt edit the APPs


Need to reall set this up.


There is an APPs table with description.

I want to be able to select the apps that are on that server, not type it in.




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
