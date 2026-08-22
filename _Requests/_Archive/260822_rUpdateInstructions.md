# rUpdateInstructions — reconcile docs, rename to BdRAIGUI, add request-creation UI, push to GitHub

**Asked (part 1):** update `_Instructions/Requests.md` to describe the
request-intake convention, and the code if required.

**Found:** `_Instructions/Requests.md` already documents the convention
actually in use (numbered `rN.md`/`rN/`, first-line `READY`/`NOT READY`,
`x`-prefix ignore, `_`-prefix archive) — that reconciliation happened in
an earlier pass. No further doc or code change needed for part 1.

**Asked (part 2):** update `_Instructions/BdRGUI.md`, rename everything
named BdRGUI to BdRAIGUI (files, code, page text), add a way to create a
`.md` request (optionally a folder with attachments) from the dashboard
UI, and get this repo pushing to GitHub under bDotRad.

**Done:**
- Renamed throughout: `_Instructions/BdRGUI.md` → `BdRAIGUI.md`,
  `systemd/bdrgui-*.service` → `bdraigui-*.service`, `nginx/bdrgui.conf`
  → `bdraigui.conf`, all `BdRGUI`/`bdrgui` text in `README.md`,
  `app/templates/index.html` (title, h1, alt text), `app/scheduler.py`
  comment. Project directory itself renamed
  `~/projects/_BdRGUI` → `~/projects/_BdRAIGUI` (confirmed with Brad
  first since the dashboard service was live against the old path).
- Added `common.create_request_file()` / `create_request_folder()` +
  `POST /api/requests/<project>` in `dashboard.py`: a "+ Request" button
  on each project card opens a modal (textarea, READY checkbox, optional
  file attachments). No attachments → writes `_Requests/rN.md`;
  attachments present → makes `_Requests/rN/request.md` + files.
  Numbering auto-increments per project by scanning existing `rN`
  entries. This is step one toward the "drop a `.md` file somewhere over
  Tailscale and the system grabs it" goal — the drop-off is now a web
  form reachable over the existing nginx/Tailscale path instead of
  needing a terminal; an unattended folder-watcher intake was already
  noted as deferred in `_Instructions/Requests.md` and stays deferred.
- Set up a GitHub deploy key (`~/.ssh/bdraigui_deploy_key`, alias
  `github.com-bdraigui` in `~/.ssh/config`) scoped to `bDotRad/BdRAIGUI`,
  added `origin` remote, committed, and pushed.
- Smoke-tested the new endpoint via Flask's test client: plain-file
  request, folder+attachment request, unknown project (404), empty
  content (400) — all behaved as expected. Verified `/` still renders
  with the new modal markup and BdRAIGUI branding.

**Outcome:** done and pushed. One follow-up needs Brad's `sudo` (same
pattern as prior requests — no passwordless sudo available):
```
sudo rm /etc/systemd/system/bdrgui-dashboard.service
sudo cp systemd/bdraigui-dashboard.service systemd/bdraigui-scheduler.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl disable bdrgui-dashboard 2>/dev/null
sudo systemctl enable --now bdraigui-dashboard bdraigui-scheduler
sudo cp nginx/bdraigui.conf /etc/nginx/sites-available/bdraigui
sudo ln -sf /etc/nginx/sites-available/bdraigui /etc/nginx/sites-enabled/bdraigui
sudo rm -f /etc/nginx/sites-enabled/bdrgui
sudo nginx -t && sudo systemctl reload nginx
```
Until that's run, the live dashboard is serving the old code from memory
off the now-renamed directory (still works — same inode — but won't
pick up these changes, including the new + Request button, until
restarted).
