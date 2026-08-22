#!/usr/bin/env python3
"""
Claude Code project dashboard -- display + rotation selection only.

All the round-robin scanning/switching logic lives in scheduler.py, a
separate always-on process. This app just:
  - shows each project's status (git, pending request count)
  - shows which project the scheduler currently has active, and its phase
    (processing / waiting / hibernating)
  - lets you tick which projects are in the scheduler's rotation pool
  - shows a recent activity log (when things last got picked up)
  - if a project has left SQL to run (e.g. for Supabase) in
    .claude-status/sql_output.txt, shows it in a copyable window

Run:
  python3 dashboard.py
Then open http://<pi-ip>:8420
"""

from flask import Flask, abort, jsonify, render_template, request

import common

app = Flask(__name__)


# ---- Routes -------------------------------------------------------------------

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/status")
def api_status():
    scheduler = common.load_scheduler_state()
    selected = set(common.load_selected())
    active_project = scheduler.get("active_project")

    projects = []
    for name in common.list_projects():
        status = common.read_status(name)
        ready, total = common.scan_requests(name)
        sql_path = common.find_sql_output(name)
        projects.append({
            "name": name,
            "in_rotation": name in selected,
            "is_active": active_project == name,
            "phase": scheduler.get("phase") if active_project == name else None,
            "current_task": status.get("current_task"),
            "last_active_relative": common.relative_time(status.get("last_active")),
            "pending_requests": ready,
            "total_requests": total,
            "last_commit": common.last_commit(name),
            "has_sql": sql_path is not None,
            "sql_updated_relative": common.file_mtime_relative(sql_path) if sql_path else None,
        })

    return jsonify({
        "active_project": active_project,
        "phase": scheduler.get("phase"),
        "scheduler_last_update": scheduler.get("last_update"),
        "projects": projects,
    })


@app.route("/api/selected", methods=["POST"])
def api_select():
    data = request.get_json(force=True)
    project = data.get("project")
    want_selected = bool(data.get("selected"))

    if project not in common.list_projects():
        return jsonify({"ok": False, "error": "unknown project"}), 404

    selected = common.load_selected()
    if want_selected and project not in selected:
        selected.append(project)
    elif not want_selected and project in selected:
        selected.remove(project)
    common.save_selected(selected)
    return jsonify({"ok": True, "selected": selected})


@app.route("/api/requests/<project>", methods=["POST"])
def api_create_request(project):
    if project not in common.list_projects():
        return jsonify({"ok": False, "error": "unknown project"}), 404

    content = (request.form.get("content") or "").strip()
    if not content:
        return jsonify({"ok": False, "error": "content is required"}), 400
    ready = request.form.get("ready") == "1"
    attachments = [f for f in request.files.getlist("attachments") if f.filename]

    if attachments:
        folder = common.create_request_folder(project, content, ready, attachments)
        common.log_event(project, "request_created", detail=folder.name)
        return jsonify({"ok": True, "created": folder.name, "kind": "folder"})

    path = common.create_request_file(project, content, ready)
    common.log_event(project, "request_created", detail=path.name)
    return jsonify({"ok": True, "created": path.name, "kind": "file"})


@app.route("/api/log")
def api_log():
    project = request.args.get("project") or None
    limit = min(int(request.args.get("limit", 50)), 200)
    return jsonify({"entries": common.read_log(limit=limit, project=project)})


@app.route("/api/sql/<project>")
def api_sql_get(project):
    if project not in common.list_projects():
        abort(404)
    sql_path = common.find_sql_output(project)
    if sql_path is None:
        return jsonify({"content": None})
    try:
        content = sql_path.read_text()
    except OSError:
        abort(500)
    return jsonify({
        "content": content,
        "filename": sql_path.name,
        "updated": common.file_mtime_relative(sql_path),
    })


@app.route("/api/sql/<project>/clear", methods=["POST"])
def api_sql_clear(project):
    if project not in common.list_projects():
        abort(404)
    sql_path = common.find_sql_output(project)
    if sql_path is not None:
        try:
            sql_path.unlink()
        except OSError:
            abort(500)
    return jsonify({"ok": True})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8420, debug=False)
