## What was asked

Brad wants to stop pushing straight to GitHub from live "app server"
machines (e.g. `BdRSrvAMI`, which runs PlanBdRad and BdRAMAssist).
Instead: the app server should drop a changed file onto the dev server
(BdRDev), a Claude session here folds it into the real tracked source
and pushes it properly, and the app server pulls the result back down.
Expected to be rare -- "it shouldn't happen often."

## What was found

- No existing convention covered this direction. `_Requests/` already
  gives BdRDev a working "drop a file, get it picked up and processed,
  archive when done" pattern, so the new convention reuses that rather
  than inventing separate automation.
- `_Instructions/SSH.md`'s current inventory confirms the concern is
  real: at least one app-server-side deploy key
  (`id_ed25519_bdramassist` on BdRSrvAMI) is already correctly
  read-only, but PlanBdRad's app-server-side key
  (`id_ed25519_planbdrad`, referenced only in passing in SSH.md) has
  unconfirmed permissions, and SSH.md separately flags an unexplained
  trusted key (comment `PlanBdRad`) already sitting in BdRDev's own
  `~/.ssh/authorized_keys` that doesn't match any known private key --
  possibly a leftover attempt at exactly the app-server -> BdRDev
  direction this convention now needs.
- No SSH key/path currently exists for an app server to actually drop a
  file onto BdRDev (the `scp`/`rsync` direction). This is the concrete
  gap standing between "convention documented" and "convention usable."

## What was done

Wrote up the convention in a new doc, `_Instructions/AppServerSync.md`:

- **Drop folder**: each project that's also deployed to an app server
  gets `~/projects/<name>/_AppServerDrops/` on BdRDev, parallel to
  `_Requests/`, created only when first needed. The app server places
  changed file(s) there, named to mirror their path inside the repo
  (e.g. `_AppServerDrops/app/scheduler.py`). Recommended to be
  `.gitignore`d -- it's a raw drop, not a vetted commit.
- **Trigger**: alongside the dropped file(s), a normal
  `_Requests/rAppServerChange ....md` request gets created (`READY`),
  describing what changed and pointing at the drop -- this reuses the
  scheduler's existing `_Requests/` wake trigger instead of adding a
  new watcher/daemon, matching "shouldn't happen often" = manual/
  on-request, not automated.
- **Dev-side handling**: read the request, diff the drop against the
  real tracked file, fold the change in (by hand, or hand off to
  `web-dev-expert`/`supabase-sql-expert` if non-trivial), commit and
  push through the normal flow, delete the file from
  `_AppServerDrops/`, archive the request -- same lifecycle as any
  other `_Requests/` item.
- **App-server-side afterward**: plain `git pull`. Flagged, not
  resolved (out of scope for this pass, no access to BdRSrvAMI from
  this repo): PlanBdRad's app-server pull-key permissions are
  unconfirmed; any remaining push-capable app-server credential should
  be revoked/downgraded once a project adopts this convention; and the
  app-server -> BdRDev drop-transport key doesn't exist yet (the
  unexplained `PlanBdRad`-labeled key already trusted in BdRDev's
  `authorized_keys`, noted in SSH.md, may be a prior attempt at this
  but is unconfirmed).

Cross-referenced the new doc from `_Instructions/BdRDev.md` (the
orchestration doc copied into other projects) and `README.md`'s
conventions list, so a newcomer session in any project can find it.

## Outcome

Convention designed and documented; no code changed, nothing configured
on any remote machine (intentionally out of scope for this pass, per
the request). Actually using the convention still needs a follow-up:
setting up (or confirming/repurposing) an app-server -> BdRDev SSH key
for the drop step, and confirming PlanBdRad's existing app-server key
is read-only -- both require hands-on access to BdRSrvAMI and are left
as open items in `_Instructions/AppServerSync.md` rather than guessed
at here.

---

## Original request (verbatim)

READY

Instead of pushing from app servers, I would rather funnel it through the dev server.

I think the best way is for the app server to drop files in the dev project foler. then let the dev system read, update, push and then the app server pull.

it shouldnt happed often, its just sometimes a change might be made on the app server
