# 260828 — Full-width page + inline-editable Ecosystem 2 grid

**Processed:** 2026-08-28 12:53
**Outcome:** Built + deployed (dashboard SIGKILL-restarted, PID 136079 →
143980, verified via `curl`). All changes in `app/templates/index.html`.

## What was asked

Screenshot of the **Ecosystem 2** tab (the server grid), plus:

> Can you make the web page full screen. Its like this is a mobile app
> version. That table should be full size. I also want to be able to edit
> the table and update the values.

This is the same "why is it so narrow / tablet-sized" complaint as
[[260826_2053_rWebDesignWidth]], but that pass only widened the Admin tab
(480 → 680) because that was the only genuinely phone-width panel at the
time. Since then the **Ecosystem**, **Ecosystem 2**, and **Fleet** panels
were each capped at `max-width: 1120px`, and the Ecosystem 2 grid was
horizontally scrolling inside that cap instead of using the screen — which
on a wide monitor reads exactly like a cramped mobile layout.

## What was done

**Full width (CSS)**
- `#ecosystem-panel` and the Ecosystem 2 panel: `max-width: 1120px` →
  `max-width: none`.
- `#fleet-panel`: `max-width: 1120px` → `max-width: none` (it also carries
  `.admin-panel-box`'s 680px cap, which the id rule already overrode).
- Ecosystem 2 `<div id="ecosystem-panel">` was a **duplicate id** (the
  real `#ecosystem-panel` is on the Ecosystem tab). Renamed to
  `#ecosystem2-panel` and folded into the same CSS rule.
- `.eco2-table`: `min-width: 100%` → `width: 100%` so the grid fills the
  now-unconstrained panel. `.eco2-scroll` keeps `overflow-x: auto` so it
  still scrolls gracefully on a small screen.
- Left the Admin tab (settings form, 680px) and the Projects grid
  (`auto-fill` columns, already full-width) alone.

**Editable Ecosystem 2 grid (HTML + JS)**
- Every server cell is now editable in place:
  - Text cells (`name`, `address`, `host`, `ram`, `disk`, `os`) are
    `contenteditable`; Enter commits (blurs) instead of inserting a
    newline.
  - New **Prov** column + the Claude / Nginx / Supabase / SQL Lite cells
    are Y/N toggles — click to flip.
  - **Other** and **Apps** columns stay read-only: both are derived
    (Other from the free-text `software` string, Apps from the App rows
    whose `server` matches), and a hint under the table says so.
- A **Save changes** / **Revert** button pair + status line under the
  grid. Save calls the existing `POST /api/ecosystem` — the same endpoint
  and payload shape the Fleet tab already uses — so it pushes to Supabase
  when reachable and always mirrors to `state/ecosystem.json`. Status line
  shows "Unsaved changes" while editing and reports which store the save
  landed in.
- `eco2EditCell` / `eco2YnCell` / `eco2ToggleYn` / `eco2Dirty` /
  `eco2Sync` / `saveEco2` added; `renderEco2()` rewritten to emit the
  editable cells. Still re-rendered from `renderEcoView()` and
  `switchTab('ecosystem2')` as before, so a Fleet-tab save refreshes it.

**Deploy:** `kill -9 136079` (systemd `Restart=on-failure` relaunch, per
this project's no-sudo / no-autoreload convention — see CLAUDE.md and
[[260822_1633_rArchivePanelRestart]]). Waited for `200` on `/`, confirmed
the served HTML contains `eco2EditCell` / `saveEco2` / `#ecosystem2-panel`
/ `max-width: none`, and that a round-trip `GET`→`POST` on
`/api/ecosystem` returns 200 and leaves `state/ecosystem.json` byte-identical.
Scheduler left untouched.

**Note on source:** the dev box currently can't reach the Pi's self-hosted
Supabase, so the grid shows "source: local JSON (Supabase unreachable)"
and saves land in `state/ecosystem.json`. That's the existing fallback
behaviour, not a regression from this change — it'll write through to
Supabase again whenever the Pi is reachable.

## Files touched

- `app/templates/index.html`

## Original request (verbatim)

```
READY

Can you make the web page full screen. Its like this is a mobile app version.

that table should be full size. I also want to be able to edit the table and update the values
```

(Original was a folder request, `rFull Page/`, with a screenshot
`2026-08-28_18-18-30.PNG` of the narrow, horizontally-scrolling Ecosystem
2 grid — not preserved; described above.)
