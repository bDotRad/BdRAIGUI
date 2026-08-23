## What was done

Brad's original ask ("change title text to yellow") turned mid-message
into a bigger request: an admin-editable colour palette for the whole
site, not just a one-off title colour tweak.

On picking this up, the backend and CSS plumbing for exactly this
feature were already sitting uncommitted in the working tree (started
in an earlier, unfinished pass — `app/common.py` had `DEFAULT_THEME`,
`load_theme()`/`save_theme()` with hex validation and a `state/
theme.json` allow-list; `app/dashboard.py` had `/api/admin/theme`
(GET/POST) and `/api/admin/theme/reset`; `index.html` had the `:root`
CSS custom properties and `#palette-grid`/`.palette-row` styling). What
was missing was the actual Admin-tab UI and the JS to drive it, so that
part was completed:

- Added a "Colour palette" section to the Admin tab: one row per
  themeable variable (Background, Card background, Card border, Text,
  Text (dim), Accent, Title text), each with a paired colour swatch +
  hex text input, plus Save / Reset to defaults buttons and a status
  line.
- Wired the inputs to `document.documentElement.style.setProperty` for
  live preview as you pick a colour, `POST /api/admin/theme` on Save,
  and `POST /api/admin/theme/reset` on Reset.
- `h1` (the site title) now reads `color: var(--title-color)`, so
  Brad's literal first ask (yellow title) is satisfied by setting that
  one swatch — but every other swatch is equally editable now.

Verified end-to-end on a scratch Flask instance (separate port, temp
`STATE_DIR`, no `sudo`/systemd involved) before touching anything live:
page renders, GET returns defaults, POST persists and the new colour
shows up in the rendered `<style>` block, invalid hex is rejected with
a 400, and reset restores defaults. No `state/theme.json` was left
behind by the test run.

Restarted the live `bdraigui-dashboard` process via `kill -9` (per
CLAUDE.md — SIGTERM doesn't trigger `Restart=on-failure`, SIGKILL does;
no sudo available to this session) so the change is actually live, not
just committed. Confirmed via `curl` against port 8420 post-restart:
`/` returns 200 and includes the palette markup, `/api/admin/theme`
returns 200 with the current (default) palette.

No outstanding blockers. Fixed, deployed, and verified live.

## Original request

READY

Change title text to yellow. Actually. In admin, let me set a colour pallet for the website
