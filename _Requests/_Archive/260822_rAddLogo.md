# rAddLogo — add the rat logo

**Asked:** add the rat logo to the top right of the page.

**Done:** copied `RatImage.png` into `app/static/rat-logo.png` (served by
Flask's default `/static/` route) and added a small fixed-position badge
in `app/templates/index.html` — 44px circle, top-right corner, `z-index`
above the grid so it stays visible while scrolling.

**Outcome:** done. Verified via Flask's test client (index renders the
tag, `/static/rat-logo.png` returns 200) before touching the live
service. Needs `sudo systemctl restart bdrgui-dashboard` to pick it up
since the service runs with `debug=False` (no autoreload) — couldn't run
that myself (no passwordless sudo), left for Brad.
