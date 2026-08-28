#!/usr/bin/env python3
"""SQLite store for srvhome deploy history.

One table: `deploys` - one row per (app, sha) this box has ever had
checked out. `recorded_at` is when srvhome learned about it: the real
pull time for rows written by the git post-merge hook, or the commit
time for rows created by the initial back-fill (`backfilled = 1`).
"""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone

SCHEMA = """
CREATE TABLE IF NOT EXISTS deploys (
    id          INTEGER PRIMARY KEY,
    app         TEXT NOT NULL,
    sha         TEXT NOT NULL,          -- 7-char short SHA
    subject     TEXT,                   -- commit title
    body        TEXT,                   -- commit description
    committed_at TEXT,                  -- ISO-8601, commit author date
    recorded_at TEXT NOT NULL,          -- ISO-8601, when srvhome recorded it
    backfilled  INTEGER NOT NULL DEFAULT 0,
    UNIQUE(app, sha)
);
CREATE INDEX IF NOT EXISTS idx_deploys_app_time ON deploys(app, recorded_at DESC);
"""


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def connect(db_path: str) -> sqlite3.Connection:
    con = sqlite3.connect(db_path, timeout=10)
    con.row_factory = sqlite3.Row
    con.executescript(SCHEMA)
    con.commit()
    return con


def record(con: sqlite3.Connection, app: str, sha: str, subject: str,
           body: str, committed_at: str, *, backfilled: bool = False,
           recorded_at: str | None = None) -> bool:
    """Insert a deploy row. Returns True if it was new.

    Idempotent on (app, sha): a repeated pull of the same SHA is ignored,
    so the per-minute keepalive / re-runs never create duplicates.
    """
    cur = con.execute(
        """INSERT OR IGNORE INTO deploys
           (app, sha, subject, body, committed_at, recorded_at, backfilled)
           VALUES (?,?,?,?,?,?,?)""",
        (app, sha, subject, body, committed_at,
         recorded_at or now_iso(), 1 if backfilled else 0),
    )
    con.commit()
    return cur.rowcount > 0


def history_for(con: sqlite3.Connection, app: str, limit: int = 40) -> list[dict]:
    rows = con.execute(
        """SELECT sha, subject, body, committed_at, recorded_at, backfilled
           FROM deploys WHERE app = ?
           ORDER BY recorded_at DESC, id DESC LIMIT ?""",
        (app, limit),
    ).fetchall()
    return [dict(r) for r in rows]


def latest_for(con: sqlite3.Connection, app: str) -> dict | None:
    row = con.execute(
        """SELECT sha, subject, body, committed_at, recorded_at, backfilled
           FROM deploys WHERE app = ?
           ORDER BY recorded_at DESC, id DESC LIMIT 1""",
        (app,),
    ).fetchone()
    return dict(row) if row else None
