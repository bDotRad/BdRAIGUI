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

  if [ "$before" = "$after" ]; then
    echo "  up to date @ ${after:0:7}"
    return
  fi
  echo "  ${before:0:7} -> ${after:0:7}"

  # migrations added by this pull, applied oldest-first
  local migs
  migs="$(git diff --name-only --diff-filter=A "$before" "$after" -- supabase/migrations \
          | grep '\.sql$' | sort)"
  if [ -n "$migs" ]; then
    while IFS= read -r m; do
      echo "  -- applying $m"
      if ! docker exec -i "$DB_CONTAINER" psql -U postgres -v ON_ERROR_STOP=1 < "$m"; then
        echo "  !! migration failed: $m -- stopping"
        rc=1; return
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
