# Fleet data editor — editable back-end for project/server specs

**Asked:** Brad wanted "a basic DB in the back end with a simple web page
to update specs of the various projects" — editing the Ecosystem tab's
fleet layout by hand (markdown/HTML + a request per change, e.g. commit
8969930 "AMI server is now Raspberry Pi 8GB") was too cumbersome; he
wants dropdowns to change settings.

**Clarified with Brad (3 questions):**
- Scope: **both** servers + projects + apps, one data store.
- Storage: **JSON file in `state/`** (consistent with the app's existing
  "DB: none (JSON state files)" design — not SQLite).
- Edit UI: **a new settings tab**, separate from the read-only Ecosystem
  diagram.

**What changed:**

- `app/common.py`
  - New `state/ecosystem.json` store. `DEFAULT_ECOSYSTEM` is the seed
    (reproduces exactly what the Ecosystem tab showed as of 2026-08-28);
    `load_ecosystem()` writes it on first use, then the file is the
    source of truth. `save_ecosystem()` + `_normalize_ecosystem()`
    coerce/validate the shape (every field present, right type, unknown
    keys dropped). `ECOSYSTEM_FIELD_OPTIONS` holds the dropdown
    suggestions.
  - Data model: `servers[]` (name, tag, address, os, ram, disk,
    software, git notes, provisioned, dev_host), `apps[]` (name, server,
    tag, web_address, db, planned), `projects[]` (name, exists, agents),
    plus a free-text `notes` string.
- `app/dashboard.py` — `GET /api/ecosystem` (data + options), `POST
  /api/ecosystem` (save whole object). Logs `ecosystem_updated`.
- `app/templates/index.html`
  - New **Fleet** tab: form editor with text fields, `<datalist>`
    dropdowns (OS / RAM / disk / software / DB — free text still
    allowed, since existing values carry parentheticals like
    "none (JSON state files)"), checkboxes for the booleans, and
    add/remove per row. Save posts the whole object.
  - Ecosystem tab: the hard-coded fleet-diagram HTML and the
    servers→projects tree are **removed**; both now render client-side
    from the JSON (`buildDiagram()` / `buildTree()`), and the "Not yet
    real" prose is now the editable `notes` block.
  - `switchTab()` rewritten to a loop (handles the 5th tab) and
    lazy-loads the ecosystem data on first visit.
- `README.md` — new "Ecosystem / fleet data" bullet under "Conventions
  this implements".

Note: the generated tree consolidates a couple of small stale
discrepancies the old hand-written copy had (it listed generic agent
names for PlanBdRad/BdRIS and "SQL Lite Expert" for BdRBirdDetector;
the diagram's domain-specific names are now the single source, with the
naming caveat kept in the notes block).

**Verified:** `app/common.py` / `app/dashboard.py` parse; `load_ecosystem`
seeds + round-trips; Flask test client — `GET /` renders with the Fleet
tab, `GET /api/ecosystem` returns data+options, `POST` saves and
re-normalizes, bad POST → 400. JS bracket/string balance checked across
the whole `<script>` block.

**Outcome:** Code complete and pushed. **Needs Brad to restart the
services** for it to go live (touches `app/` + template; Flask runs with
no autoreload, no passwordless sudo here):

```
sudo systemctl restart bdrdev-dashboard bdrdev-scheduler
```

(scheduler restart isn't strictly required — it never reads the file —
but the Admin tab's "Restart both" does both anyway.) After restart,
check the **Fleet** tab loads, edit a field, Save, and confirm the
**Ecosystem** tab re-renders.

`state/ecosystem.json` is gitignored (all of `state/` is), so nothing
new is committed there — the seed is in `common.py`.

---

## Original request (`rSimple SQL with Web Interface.md`)

```
READY

I think this Dev page needs a basic DB in the back end with a simple web page to update specs of the various projects. Its too cumbersome to do through this. i can just use drop downs to change settings
```
