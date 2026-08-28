# rFLEET — "Ecosystem 2" server grid (spreadsheet-style table)

**Processed:** 2026-08-28 11:35
**Outcome:** Built + deployed (dashboard SIGKILL-restarted, verified via
`curl`). One follow-up split off as `_Requests/rFLEET-db-schema.md`
(`WAITING RESPONSE`).

## What was asked

"Id like a table like the attached." The attachment
(`2026-08-28_15-42-30.PNG`, kept in this folder) shows the fleet as a
spreadsheet:

    Name | Address | Hardware{Host|Ram|Disk} | Software{OS|Claude|Nginx|Supabase|SQL Lite} | Apps

Three decisions were put back to Brad and answered inline:

1. **Where does it go?** → "Make Ecosystem 2 for now in case its shite" —
   i.e. a *new* tab, leave the existing Ecosystem tab alone.
2. **Software Y/N columns** → wants a Yes/No cell per package so a human
   can scan down what's on what. Also wants the real backing store to be
   a proper Supabase schema (Projects / Software / ProjectSoftware),
   designed by the SQL agent — "not just json files".
3. **Host column** → yes, needs a Host field. New fleet naming rule:
   VM hosts `BdRVSrv…`, Raspberry Pi hosts `BdRPiSrv…`; `BdRSrvDev` →
   `BdRVSrvDev`.

## What was done

**Data model (`app/common.py`)**
- Server objects gained: `host` (free text, datalist VM / Physical /
  Raspberry Pi) and four booleans `claude` / `nginx` / `supabase` /
  `sqlite`.
- `_normalize_ecosystem()` back-fills the booleans from the free-text
  `software` string when a server predates the keys, so any older
  `ecosystem.json` upgrades cleanly on first load. The free-text
  `software` field is kept (it feeds the existing Ecosystem tab's
  diagram/tree and the new "Other" column).
- `ECOSYSTEM_FIELD_OPTIONS["host"]` added for the editor datalist.
- `DEFAULT_ECOSYSTEM` + `state/ecosystem.json` refreshed: dev box renamed
  `BdRSrvDev` → `BdRVSrvDev` (and the app row's `server` ref with it),
  `host` set per box (VM / Raspberry Pi), booleans set explicitly, and
  the `notes` blurb updated to say the rename is display-only so far.

**UI (`app/templates/index.html`)**
- New **Ecosystem 2** tab between Ecosystem and Fleet. Renders a
  horizontally-scrolling table with the grouped `Hardware` / `Software`
  header from the mock: Name · Address · Host · RAM · Disk · OS ·
  Claude · Nginx · Supabase · SQL Lite · Other · Apps. Y cells are
  green, N cells dim; unprovisioned servers are greyed with a tag. The
  Apps cell lists apps whose `server` matches. "Other" shows any
  free-text software token not covered by a Y/N column (e.g. Scheduler).
- Fleet tab editor: server rows now have a Host field + Claude / Nginx /
  Supabase / SQL Lite checkboxes; `fleetAdd('servers')` seeds them.
- `renderEco2()` is called from `renderEcoView()` (so Save/Revert
  refresh it) and from `switchTab('ecosystem2')`.

**Deploy:** `kill -9` on the dashboard pid (systemd relaunch), waited
for `200` on `/`, verified `/api/ecosystem` returns the new fields and
the page contains the "Ecosystem 2" tab + `renderEco2`. Scheduler left
untouched.

## What was NOT done (see `_Requests/rFLEET-db-schema.md`)

- **The Supabase schema.** BdRDev has no database, no Supabase client,
  no connection string today — standing one up needs Brad's answers
  (which Supabase instance, is a hard DB dependency OK, schema scope,
  migration tooling). Left as `WAITING RESPONSE`.
- **The real fleet rename.** Only the ecosystem *data* says `BdRVSrvDev`.
  The machine hostname, SSH key names (`_Instructions/SSH.md` already
  flags the app-name-vs-hostname question as open), `~/.ssh/config`
  aliases, systemd units, nginx `server_name`, and docs still say
  `BdRDev` / `BdRSrvDev`. That rollout ripples across every project on
  the Pi and needs a dedicated pass with Brad present — not a
  scan-requests job.

## Files touched

- `app/common.py`
- `app/templates/index.html`
- `state/ecosystem.json`
- `_Requests/rFLEET-db-schema.md` (new, WAITING RESPONSE)

---

## Original request (verbatim)

```
READY

Id like a table like the attached

---

## Blocked — need answers before building (added by Claude 2026-08-28)

The attached `2026-08-28_15-42-30.PNG` shows servers as a spreadsheet:

    Name | Address | Hardware{ Host | Ram | Disk } | Software{ OS | Claude | Nginx | Supabase | SQL Lite } | Apps
    BdRVSrvDev | 192.168.100.10 | VM | 8 | 100 | Ubuntu Server 24 | Y | Y | Y | (blank) | BdRDev

This is a data-model + UI change to the Fleet/Ecosystem feature. Three
things I can't decide for you — answer inline (edit each `A:` line) and
flip the first line back to `READY`:

**1. Where does the table go?**
  - (a) Replace the Ecosystem tab's server *card diagram* with this
    table; keep the "Servers → software / projects" text tree and the
    generic-folder-structure box below it.
  - (b) Keep the card diagram; add the table as a new block above it.
  - (c) Replace the cards with the table AND rebuild the **Fleet** tab
    editor as an editable grid in the same column layout.
  A: Make Ecosystem 2 for now in case its shite

**2. The "Software" group is Y/N columns. How should the data change?**
  Right now each server has one free-text `software` string
  (e.g. "Claude Code · Nginx · Supabase").
  - (a) Add booleans `claude / nginx / supabase / sqlite` for the
    checkmark columns, keep the free-text `software` field too.
  - (b) Drop the free-text field; derive the diagram/tree wording from
    the booleans (cleaner, changes some wording).
  - (c) Make the column list itself editable data (e.g.
    `software_columns: ["Claude","Nginx","Supabase","SQL Lite"]` +
    per-server `runs: [...]`) so columns can be added without a code
    change.
  A: I want yes no for each software so its easy for a human to scan down whats on what.
     the actual DB can be set up differently with a table like ProjectSoftware with a Proj to SW ID link
Tables might be
Projects
Software

Then software is ID, Name, Description

Then a table ProjectSoftware
ProjectID, SoftwareID


I need the SQL Agent to provide a good quality well thought out schema, not jsut shit.
Needs to be in supabase, not jsut json files.





**3. The "Host" column shows "VM", and the sample row names the dev box
   "BdRVSrvDev" with ram 8 / disk 100 / OS "Ubuntu Server 24".**
  - (a) Add a `host` field (VM / Physical / Raspberry Pi / …) to the
    model + table; treat the screenshot row as a *layout mock only* —
    don't touch existing server names/specs.
  - (b) Add the `host` field AND apply the row: rename `BdRSrvDev` →
    `BdRVSrvDev`, set host=VM, ram=8, disk=100, os="Ubuntu Server 24".
  - (c) No Host column — columns are Name | Address | Ram | Disk | OS |
    Claude | Nginx | Supabase | SQL Lite | Apps.
  A:This was just an example. But it needs Host.

The general rule is a VM is BdRVSrv#######
and RPI is BdRPiSrv#######

So i need to update names of things.

BdRSrvDev will become BdRVSrvDev

(Note: `CLAUDE.md` now says the dev host is **BdRSrvDev** and the old VM
`BdRSrvAMI` at 192.168.100.20 is decommissioned — so the ecosystem.json
data is already somewhat stale and may want a refresh in the same pass.)
```
