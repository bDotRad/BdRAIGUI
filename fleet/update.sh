#!/usr/bin/env bash
# update.sh -- pull + apply new migrations + rebuild an app on this box.
# Manual stand-in for the srvhome dashboard "Update" button.
#
#   ./update.sh PlanBdRad
#   ./update.sh BdRAMAssist
#   ./update.sh all          (or no argument)
#
# For each app: git pull --ff-only; if the pull brought new
# supabase/migrations/*.sql files, apply them in order (psql, stop on
# error); then rebuild app/ if anything changed. Safe to re-run -- a
# no-op pull skips the migrate + build.
set -uo pipefail

APPS=(PlanBdRad BdRAMAssist)
PROJECTS="$HOME/projects"
DB_CONTAINER="supabase-db"
export PATH="$HOME/.local/bin:$PATH"     # nvm-installed node/npm

rc=0

update_one() {
  local app="$1" repo="$PROJECTS/$1"
  echo "=== $app ==="
  if [ ! -d "$repo/.git" ]; then echo "  !! no git repo at $repo"; rc=1; return; fi
  cd "$repo" || { rc=1; return; }

  local before after
  before="$(git rev-parse HEAD)"
  if ! git pull --ff-only; then
    echo "  !! git pull failed (diverged local checkout?) -- skipping $app"
    rc=1; return
  fi
  after="$(git rev-parse HEAD)"

  # Is the served bundle behind HEAD? app/dist/build-info.json carries the
  # SHA it was built from. A stale dist after a no-op pull is the case the
  # old "before == after -> return" path silently skipped for ~8h.
  local built_sha stale_build=0
  built_sha="$(sed -n 's/.*"sha"[: ]*"\([0-9a-f]\{7,\}\)".*/\1/p' app/dist/build-info.json 2>/dev/null | head -1)"
  if [ -f app/package.json ]; then
    if [ -z "$built_sha" ] || [ "${after:0:${#built_sha}}" != "$built_sha" ]; then
      stale_build=1
    fi
  fi

  if [ "$before" = "$after" ] && [ "$stale_build" -eq 0 ]; then
    echo "  up to date @ ${after:0:7} (dist matches)"
    return
  fi
  if [ "$before" = "$after" ]; then
    echo "  @ ${after:0:7} — no new commits, but dist is at ${built_sha:-none}; rebuilding"
  else
    echo "  ${before:0:7} -> ${after:0:7}"
  fi

  # migrations added by this pull, applied oldest-first. A ledger table
  # (public._srvhome_migrations) records what's already been applied, so a
  # migration that was run by hand earlier is skipped instead of erroring
  # under ON_ERROR_STOP and killing the build (that bug served a stale
  # bundle for ~8h on 2026-08-30).
  docker exec -i "$DB_CONTAINER" psql -U postgres -q <<'SQL' 2>/dev/null || true
CREATE TABLE IF NOT EXISTS public._srvhome_migrations (
  app text NOT NULL, filename text NOT NULL,
  applied_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (app, filename));
SQL
  local migs
  migs="$(git diff --name-only --diff-filter=A "$before" "$after" -- supabase/migrations \
          | grep '\.sql$' | sort)"
  if [ -n "$migs" ]; then
    while IFS= read -r m; do
      local base done_already
      base="$(basename "$m")"
      done_already="$(docker exec -i "$DB_CONTAINER" psql -U postgres -tA -c \
        "select 1 from public._srvhome_migrations where app='$app' and filename='$base'" 2>/dev/null)"
      if [ "$done_already" = "1" ]; then
        echo "  -- skip $base (already applied)"
        continue
      fi
      echo "  -- applying $base"
      if docker exec -i "$DB_CONTAINER" psql -U postgres -v ON_ERROR_STOP=1 < "$m"; then
        docker exec -i "$DB_CONTAINER" psql -U postgres -c \
          "insert into public._srvhome_migrations(app,filename) values('$app','$base') on conflict do nothing" >/dev/null 2>&1 || true
      else
        echo "  !! migration failed: $base -- recorded rc=1, continuing to build so deploy isn't frozen"
        rc=1
      fi
    done <<< "$migs"
    docker exec "$DB_CONTAINER" psql -U postgres -c "NOTIFY pgrst, 'reload schema';" >/dev/null 2>&1 || true
  fi

  # rebuild the frontend (skip build.sh -- app-specific baggage; do it directly)
  if [ -f app/package.json ]; then
    ( cd app && npm install --no-audit --no-fund --silent && npm run build ) \
      || { echo "  !! build failed for $app"; rc=1; return; }
    echo "  built @ ${after:0:7}"
  fi
}

sel="${1:-all}"
if [ "$sel" = "all" ]; then
  for a in "${APPS[@]}"; do update_one "$a"; done
else
  update_one "$sel"
fi
exit $rc
