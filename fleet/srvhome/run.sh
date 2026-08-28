#!/usr/bin/env bash
# Idempotent starter for srvhome, driven by the user crontab (per minute
# + @reboot). Starts the server only if nothing is already listening on
# its port. Safe to run any number of times.
set -euo pipefail
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PORT="$(python3 -c 'import json;print(json.load(open("'"$DIR"'/srvhome.conf.json")).get("bind_port",8610))' 2>/dev/null || echo 8610)"

if curl -s -o /dev/null "http://127.0.0.1:${PORT}/healthz" 2>/dev/null; then
  exit 0
fi

mkdir -p "$DIR/log"
nohup python3 "$DIR/srvhome.py" >>"$DIR/log/srvhome.log" 2>&1 &
echo "$(date -Is) started srvhome pid $!" >>"$DIR/log/srvhome.log"
