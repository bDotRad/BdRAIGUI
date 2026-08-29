NOT READY

# Ecosystem page consolidation

**Claimed 2026-08-30 by the Independent Claude session — being
implemented live with Brad. Do not process this from a scheduled pass.**

Both questions answered (2026-08-29): **delete the old Ecosystem tab**,
**drop the notes blob from the page** (stays in the DB).

## Brad's final spec (2026-08-30)

a. Remove the **Ecosystem** tab.
b. Remove the **Fleet** tab.
c. Rename **Ecosystem 2** → **Ecosystem**.
d. Remove the text above *and* below the table.
e. Edit button → top right of the table.
f. Add a **Projects** table below the **Servers** table:

| Col | Type |
|---|---|
| Name | text |
| PM | Y/N |
| Web | Y/N |
| DB | Y/N |
| Elec Ctrl | Y/N |
| Elec LV-HV | Y/N |
| Doco | Y/N |
| Runs on | dropdown of servers (blank = not deployed) |
| Web URL | text, rendered as a link in read mode |
| Database | `none` / `SQLite` / `Supabase` / `shares:<project>` |
| Status | `planned` / `building` / `deployed` / `live` |

Supersedes **`rFlet update`** and **`rUpdate Fleet - Add Project Table`**
(both folded in verbatim at the bottom). Does **not** cover
`rFix all of the web pages` — that's the Pi app-deployment work, a
separate concern, left in place.

- Design + rationale: `supabase/DATA_MODEL.md`
- Draft schema change: `supabase/DRAFT_fold_apps_into_projects.sql`

Flip to `READY` once the two questions below are answered.

---

## Goal

**One `Ecosystem` tab. Delete the `Fleet` tab and the old `Ecosystem`
(ASCII tree) tab.** The page holds two editable grids, both using the
standard Edit / Save / Cancel pattern with the **Edit button at the top
right**, and **no notes / blurb / explainer above them**.

### Grid 1 — Servers

Today's "Ecosystem 2" server grid, minus the derived **Apps** and
**Other** columns.

`Name` · `Address` · `Tailscale IP` · `Web` · `Prov` · `Host` · `OS` ·
`RAM` · `Disk` · `Claude` · `Nginx` · `Supabase` · `SQLite`

### Grid 2 — Projects (new)

| Col | Type |
|---|---|
| Name | text |
| PM | Y/N |
| Web | Y/N |
| DB | Y/N |
| Elec Ctrl | Y/N |
| Elec LV-HV | Y/N |
| Doco | Y/N |
| Runs on | dropdown of servers (blank = not deployed) |
| Web URL | text, rendered as a link in read mode |
| Database | `none` / `SQLite` / `Supabase` / `shares:<project>` |
| Status | `planned` / `building` / `deployed` / `live` |

PM…Doco are the dev-agent **role matrix** (Brad's spec in
`rUpdate Fleet…` below). "Runs on / Web URL / Database / Status" are the
old `apps` fields, now living on the project — see `DATA_MODEL.md` for
why `apps` folds into `projects`.

### Data source line

Keep the existing `source: supabase | json-fallback` indicator.

---

## Work

1. **[Brad — remote DDL]** Run **Part A** of
   `supabase/DRAFT_fold_apps_into_projects.sql` on the Pi (add columns +
   role tables, migrate `apps`/`project_agents` data across). Then run
   the two report queries at the bottom of that file and fix anything
   they flag by hand (free-text `db` values, unmapped agent names).

2. **`app/fleet_db.py`** — `_write_all` / `push_ecosystem`: write the new
   `projects` columns (`runs_on_server_id`, `web_url`, `database`,
   `status`) and the `project_roles` links; stop writing the `apps`
   table.

3. **`app/common.py`** — `_normalize_ecosystem` + `DEFAULT_ECOSYSTEM`:
   new project shape (`runs_on`, `web_url`, `database`, `status`,
   `roles[]`); drop the top-level `apps` list.

4. **`app/templates/index.html`** — merge the three tabs into one
   `Ecosystem` tab with the two grids above; delete `renderFleet()` and
   the old ecosystem-tree renderer; Edit button top-right on both grids;
   remove the notes blurb.

5. **[Brad — DDL + app-code ready together]** Run **Part B** of the draft
   (swap the `fleet_ecosystem_json` view), then restart the dashboard
   (`sudo systemctl restart bdrdev-dashboard`). Verify both grids load,
   edit round-trips, `source: supabase`.

6. **`_Instructions/WebUI.md`** — if the two-grid page sets a precedent
   worth documenting fleet-wide, add it.

7. **[Brad — remote DDL, after verify]** Run **Part C** of the draft
   (drop `apps`, `project_agents`, add RLS/grants for the new tables).

Steps 1, 5, 7 are remote-DDL / sudo — an unattended session must write
them into an `@@@ --- Action --- @@@` block here, not attempt them.

---

## Open questions

??? --- Question --- ???

The old **Ecosystem** tab is an ASCII tree + fleet diagram of
servers → projects. Once the two grids exist, keep it?

Options:
1. **Delete it** (recommended) — the grids carry the same information;
   a rendered diagram can come back later as its own request if missed.
2. Keep it as a **read-only** view rendered from the two grids (not
   separately editable).

Answer: 1 — delete it.

??? --------------- ???

??? --- Question --- ???

The fleet **notes** blob (`fleet_meta.notes` — the long paragraph
currently shown at the top of the Fleet / Ecosystem tabs).

Options:
1. **Drop it from the page** (recommended) — stays in the DB, just not
   shown. `rFlet update` says "just the table".
2. Keep it, **collapsed**, at the bottom of the Ecosystem page.

Answer: 1 — drop it from the page.

??? --------------- ???

===========================================================================
SUPERSEDED REQUESTS (verbatim)
===========================================================================

----- _Requests/rFlet update.md -----

READY

Get rid of the notes and the blurb at the top. i jsut want the table. move the edit button to the top right

----- _Requests/rUpdate Fleet - Add Project Table.md -----

READY

IMPORTANT.... I MEANT ECOSYSTEM 2 Page not FLEET.

I am looking to get rid of FLEET and ECOSYSTEM

Projects
     |              Dev Agents                  | Software    |
Name | PM, Web, DB, Elec Ctrl, Elec LV HV, Doco |  Web  | DB  |

Name - Text
Dev Agents - Y,N
Software - Web is the Web Address or blank. DB = SQL Lite or Supabase

(The file also carried a pasted console snapshot from 2026-08-29 15:35 —
unrelated terminal output from the rFix-all-web-pages pass, not part of
the ask; dropped here.)
