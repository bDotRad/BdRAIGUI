# Independent Claude session — 2026-08-29, fleet review + data model

Point-in-time record of a conversation Brad had with the Independent
Claude session. Not a standing instruction — a log of what was decided
and what shipped. Started as "does Supabase have a web UI on the
servers", became a review of the fleet data setup and a data-model
proposal.

## Thread by thread

**1. Does Supabase have a web interface?**
Yes — **Supabase Studio**, running on the Pi (BdRPiSrvAMI) at
`https://bdrpiami.local/`, HTTP-Basic gated (creds in the Pi's
`supabase/docker/.env`). The Pi is the only fleet machine with Supabase.
`https://bdrpiami.local/status/` (srvhome) is now live too — the Nginx
route that `CLAUDE.md` still lists as pending got added.

**2. Does BdRSrvDev (this box) have Supabase?**
No. No Docker, no database, nothing listening. It holds `supabase/`
migration *source* only. Correct — it was never meant to run one.

**3. "You've been lying that Ecosystem 2 is on Supabase, not JSON."**
Checked live: it **is** on Supabase right now. `/api/ecosystem` returns
`source: supabase`, `supabase_configured: true`; the `SUPABASE_*` env
vars are set on the running `bdrdev-dashboard` unit and process. That
string is only emitted when a live read from the Pi succeeds — a failure
reports `json-fallback`. `state/ecosystem.json` is a mirror, rewritten
on every successful read (so its fresh timestamp is expected, not a
red flag). History was genuinely murky: JSON-only for days with the env
vars commented out, earlier passes said so plainly, then a 13:09
unattended pass on 2026-08-29 declared it live.

Flagged, not yet fixed:
- **The Supabase write path (`push_ecosystem` → `_write_all`) has never
  run in production.** ~12 independent REST calls incl. DELETEs, no
  transaction. A partial failure leaves Supabase half-written and the
  next read overwrites the JSON mirror with it. Do one supervised test
  edit before trusting Save.
- **The `service_role` JWT is world-readable** via `systemctl cat
  bdrdev-dashboard`, and has been pasted into `_Requests/_Archive/*`
  files that are pushed to GitHub. Move to a `chmod 600`
  `EnvironmentFile`, rotate, scrub history.
- If the Pi goes down the dashboard silently serves stale JSON with only
  a small label change — no alert.

**4. Data model — the main outcome.** See `supabase/DATA_MODEL.md`.
Recommendation: **two entities, not three — fold `app` into `project`.**
For this fleet a project deploys exactly one app, so "app" is the
deployment facet of a project (which server, URL, database), joined by
one nullable `runs_on` FK. Today's schema has three unrelated tables
(`servers`, `projects`, `apps`) with **no link between a project and its
app** — they're matched by name string, unenforced, and it already
breaks (`BdRDev` vs `BdRDev dashboard + scheduler`).

**5. Session workflow discussion.** Captured as
`_Instructions/SessionScope.md`. Short version: fresh-per-request is the
right model; it was slow because one logical task spanned six sessions
(each clearing mid-task) and the archive notes captured "what was done"
not "what to know". Fix with right-sized requests, front-loaded
decisions, and richer handoff writeups — not more retained history.

## What shipped (BdRDev, master)

- `6ca60f0` — `supabase/DATA_MODEL.md` (proposal),
  `supabase/DRAFT_fold_apps_into_projects.sql` (draft expand/swap/
  contract migration, kept out of `migrations/` so nothing auto-runs
  it), `_Requests/rEcosystemConsolidation.md`. Deleted `rFlet update.md`
  and `rUpdate Fleet - Add Project Table.md` (text folded into the new
  request verbatim). `rFix all of the web pages.md` left in place —
  separate Pi-deploy concern.
- `4d43eb0` — `rEcosystemConsolidation` → `READY`, Brad's two answers
  applied: delete the old Ecosystem (ASCII tree) tab; drop the fleet
  notes blob from the page (stays in the DB).
- `<this commit>` — `_Instructions/SessionScope.md`, this file.

## Open / not done

- `rEcosystemConsolidation` is `READY`, waiting for the scheduler's next
  BdRDev pass. It will need Action blocks written for Brad: run the
  draft migration Parts A/B/C on the Pi, and `sudo systemctl restart
  bdrdev-dashboard`.
- The draft migration has not been run. It's coupled to app-code changes
  (`fleet_db.py`, `common.py`, `templates/index.html`) — see the
  request's work list.
- The two risks in thread 3 (untested write path, exposed key) are not
  tracked by any request yet.
- Offered but not done: a `/process-request` slash command encoding the
  request convention; a fuller "Fleet Setup Reality Check" writeup.
