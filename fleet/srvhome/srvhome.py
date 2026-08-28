#!/usr/bin/env python3
"""srvhome - per-server "what's running here" home page.

Runs on a fleet server (first: BdRPiSrvAMI / the Pi), binds to
127.0.0.1:8610, and is exposed by that box's Nginx under /status/.
It shows one tile per app the server hosts:

  * the version deployed here right now (7-char commit SHA) + its
    commit title,
  * a running/not-tracked badge (live status is deliberately deferred -
    see the request; the badge is neutral until that is wired up),
  * a history of updates - every version this box has pulled, with the
    deploy timestamp, commit title and description.

History comes from a small SQLite DB (srvhome.db) that a git
`post-merge` hook writes to on every `git pull`. On first install the DB
is back-filled from `git log` so history is not empty.

Pure Python 3 standard library - no Flask, no pip. Config: apps.json.
"""

from __future__ import annotations

import html
import json
import os
import subprocess
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(HERE, "srvhome.db")
APPS_JSON = os.path.join(HERE, "apps.json")
CONF_JSON = os.path.join(HERE, "srvhome.conf.json")

from store import connect, history_for, latest_for  # noqa: E402


def load_conf() -> dict:
    conf = {"server": os.uname().nodename, "bind_host": "127.0.0.1",
            "bind_port": 8610, "history_limit": 40}
    try:
        with open(CONF_JSON) as fh:
            conf.update(json.load(fh))
    except FileNotFoundError:
        pass
    return conf


def load_apps() -> list[dict]:
    try:
        with open(APPS_JSON) as fh:
            return json.load(fh)
    except FileNotFoundError:
        return []


def _git(path: str, *args: str) -> str:
    try:
        out = subprocess.run(
            ["git", "-C", path, *args],
            capture_output=True, text=True, timeout=10,
        )
        return out.stdout.strip() if out.returncode == 0 else ""
    except (OSError, subprocess.SubprocessError):
        return ""


def app_state(app: dict, history_limit: int) -> dict:
    """Assemble the display state for one app."""
    path = os.path.expanduser(app["path"])
    name = app["name"]
    present = os.path.isdir(os.path.join(path, ".git"))

    head_sha = _git(path, "rev-parse", "--short=7", "HEAD") if present else ""
    head_subject = _git(path, "log", "-1", "--format=%s") if present else ""
    branch = _git(path, "rev-parse", "--abbrev-ref", "HEAD") if present else ""

    con = connect(DB_PATH)
    try:
        rows = history_for(con, name, history_limit)
        latest = latest_for(con, name)
    finally:
        con.close()

    return {
        "name": name,
        "path": path,
        "present": present,
        "branch": branch,
        "head_sha": head_sha,
        "head_subject": head_subject,
        # deployed = what the DB last recorded a pull to; falls back to HEAD
        "deployed_sha": (latest or {}).get("sha", "") or head_sha,
        "deployed_at": (latest or {}).get("recorded_at", ""),
        "running": None,   # deferred - see request answer #2
        "history": rows,
    }


def full_state() -> dict:
    conf = load_conf()
    apps = load_apps()
    limit = int(conf.get("history_limit", 40))
    return {
        "server": conf.get("server") or os.uname().nodename,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "apps": [app_state(a, limit) for a in apps],
    }


# --------------------------------------------------------------------------
# rendering
# --------------------------------------------------------------------------

PAGE_CSS = """
:root{color-scheme:dark}
*{box-sizing:border-box}
body{margin:0;background:#0f1216;color:#d7dde3;
     font:15px/1.5 ui-sans-serif,system-ui,-apple-system,Segoe UI,Roboto,sans-serif}
header{padding:22px 28px;border-bottom:1px solid #232a31;background:#12171d}
header h1{margin:0;font-size:19px;letter-spacing:.3px}
header .sub{color:#8b96a1;font-size:13px;margin-top:4px}
main{padding:24px 28px;max-width:1100px;margin:0 auto}
.tile{background:#141a20;border:1px solid #232a31;border-left:4px solid #3a4550;
      border-radius:10px;padding:18px 20px;margin-bottom:22px}
.tile.is-running{border-left-color:#3fb950}
.tile.is-stopped{border-left-color:#f85149}
.tile.is-unknown{border-left-color:#d29922}
.tile.is-absent {border-left-color:#3a4550}
.tile h2{margin:0 0 2px;font-size:16px}
.row{display:flex;flex-wrap:wrap;gap:14px;align-items:baseline;margin:8px 0 14px}
.badge{font-size:12px;padding:2px 9px;border-radius:20px;border:1px solid #333d47;
       color:#aab4bf;background:#1a2129}
.badge.ok{color:#7fd18c;border-color:#2f5136;background:#132018}
.badge.off{color:#e08a8a;border-color:#5a2f2f;background:#201313}
.badge.unknown{color:#e3b341;border-color:#5c4813;background:#211c0f}
.sha{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;color:#e2c08d}
.sha.live{color:#7fd18c}
.muted{color:#8b96a1}
table{width:100%;border-collapse:collapse;font-size:13.5px}
th,td{text-align:left;padding:7px 10px;border-bottom:1px solid #202730;vertical-align:top}
th{color:#8b96a1;font-weight:600;font-size:12px;text-transform:uppercase;letter-spacing:.4px}
td.v{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;color:#e2c08d;white-space:nowrap}
td.v.live{color:#7fd18c}
td.t{white-space:nowrap;color:#9aa5b0}
td.desc{color:#9aa5b0;white-space:pre-wrap}
tr.live td{background:#122017}
tr.backfilled td.v{color:#8b96a1}
.live-tag{display:inline-block;margin-left:7px;padding:0 6px;font-size:10.5px;
          color:#7fd18c;border:1px solid #2f5136;border-radius:20px}
.empty{color:#8b96a1;font-style:italic;padding:6px 0}
footer{max-width:1100px;margin:0 auto;padding:8px 28px 40px;color:#6b7580;font-size:12px}
.legend{display:flex;gap:15px;flex-wrap:wrap;margin-bottom:10px;font-size:11.5px}
.legend span::before{content:'';display:inline-block;width:9px;height:9px;border-radius:2px;
                     margin-right:5px;vertical-align:middle;background:currentColor}
.legend .l-run{color:#3fb950}
.legend .l-stop{color:#f85149}
.legend .l-unknown{color:#d29922}
.legend .l-live{color:#7fd18c}
"""


def _fmt_ts(iso: str) -> str:
    if not iso:
        return "—"
    try:
        dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d %H:%M")
    except ValueError:
        return iso


def render_html(state: dict) -> str:
    e = html.escape
    out = [
        "<!doctype html><html lang=en><head><meta charset=utf-8>",
        "<meta name=viewport content='width=device-width,initial-scale=1'>",
        f"<title>{e(state['server'])} — running apps</title>",
        f"<style>{PAGE_CSS}</style></head><body>",
        "<header>",
        f"<h1>{e(state['server'])} — running apps</h1>",
        f"<div class=sub>Status of the apps this server hosts, and the "
        f"history of versions it has pulled. "
        f"Generated {e(_fmt_ts(state['generated_at']))} UTC.</div>",
        "</header><main>",
    ]

    if not state["apps"]:
        out.append("<p class=empty>No apps configured (see apps.json).</p>")

    for app in state["apps"]:
        if app["running"] is True:
            badge = "<span class='badge ok'>running</span>"
            tile_cls = "is-running"
        elif app["running"] is False:
            badge = "<span class='badge off'>not running</span>"
            tile_cls = "is-stopped"
        elif not app["present"]:
            badge = "<span class='badge unknown' title='live status not tracked yet'>status not tracked</span>"
            tile_cls = "is-absent"
        else:
            badge = "<span class='badge unknown' title='live status not tracked yet'>status not tracked</span>"
            tile_cls = "is-unknown"

        out.append(f"<div class='tile {tile_cls}'>")
        out.append(f"<h2>{e(app['name'])}</h2>")
        out.append("<div class=row>")
        out.append(badge)
        if app["present"]:
            out.append(
                f"<span>version <span class='sha live'>{e(app['deployed_sha'] or '?')}</span></span>"
            )
            if app["branch"]:
                out.append(f"<span class=muted>branch {e(app['branch'])}</span>")
            if app["head_subject"]:
                out.append(f"<span class=muted>&ldquo;{e(app['head_subject'])}&rdquo;</span>")
        else:
            out.append("<span class=muted>repo not present on this box</span>")
        out.append("</div>")

        rows = app["history"]
        if rows:
            out.append("<table><thead><tr><th>Version</th><th>Deployed</th>"
                       "<th>Title</th><th>Description</th></tr></thead><tbody>")
            for r in rows:
                is_live = bool(r["sha"]) and r["sha"] == app["deployed_sha"]
                row_cls = " ".join(c for c in (
                    "live" if is_live else "",
                    "backfilled" if r.get("backfilled") else "",
                ) if c)
                tr_attr = f" class='{row_cls}'" if row_cls else ""
                tag = " <span class=muted>(backfilled)</span>" if r.get("backfilled") else ""
                live_tag = " <span class=live-tag>live here</span>" if is_live else ""
                out.append(
                    f"<tr{tr_attr}>"
                    f"<td class='v{' live' if is_live else ''}'>{e(r['sha'])}{live_tag}</td>"
                    f"<td class=t>{e(_fmt_ts(r['recorded_at']))}{tag}</td>"
                    f"<td>{e(r['subject'] or '')}</td>"
                    f"<td class=desc>{e((r['body'] or '').strip())}</td>"
                    "</tr>"
                )
            out.append("</tbody></table>")
        else:
            out.append("<div class=empty>No deploy history recorded yet.</div>")
        out.append("</div>")

    out.append("</main>")
    out.append(
        "<footer>"
        "<div class=legend>"
        "<span class=l-run>running</span>"
        "<span class=l-stop>not running</span>"
        "<span class=l-unknown>status not tracked</span>"
        "<span class=l-live>version currently deployed on this box</span>"
        "</div>"
        "srvhome &middot; canonical source: BdRDev/fleet/srvhome &middot; "
        "history written by each repo's git post-merge hook</footer>"
    )
    out.append("</body></html>")
    return "".join(out)


# --------------------------------------------------------------------------
# server
# --------------------------------------------------------------------------

class Handler(BaseHTTPRequestHandler):
    server_version = "srvhome/1.0"

    def _send(self, code: int, body: bytes, ctype: str) -> None:
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        path = self.path.split("?", 1)[0].rstrip("/")
        # tolerate being mounted at / or /status
        path = path[len("/status"):] if path.startswith("/status") else path
        if path in ("", "/"):
            body = render_html(full_state()).encode()
            self._send(200, body, "text/html; charset=utf-8")
        elif path in ("/api/state", "/api"):
            body = json.dumps(full_state(), indent=2).encode()
            self._send(200, body, "application/json")
        elif path in ("/healthz", "/health"):
            self._send(200, b"ok\n", "text/plain")
        else:
            self._send(404, b"not found\n", "text/plain")

    do_HEAD = do_GET

    def log_message(self, fmt: str, *args) -> None:  # quieter logs
        pass


def main() -> None:
    conf = load_conf()
    host = conf.get("bind_host", "127.0.0.1")
    port = int(conf.get("bind_port", 8610))
    # make sure the schema exists before serving
    connect(DB_PATH).close()
    httpd = ThreadingHTTPServer((host, port), Handler)
    print(f"srvhome listening on http://{host}:{port}  (db: {DB_PATH})", flush=True)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
