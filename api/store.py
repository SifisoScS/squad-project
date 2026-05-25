"""
SQLite-backed build store (#3).

Keeps completed and failed build records on disk so they survive server
restarts. Running builds are held in the in-memory _builds dict in main.py
and persisted here when they finish.

Only the main thread (FastAPI) calls save() and load_all() — no extra locking
needed beyond SQLite's own serialised-write guarantee.
"""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path

_DB_PATH = Path("builds.db")


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(str(_DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """
    Create the builds table if it doesn't exist.
    Any build that was 'running' when the server last died is marked 'orphaned'
    so clients get an honest status rather than a build that never completes.
    """
    with _connect() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS builds (
                id        TEXT PRIMARY KEY,
                spec_name TEXT NOT NULL,
                status    TEXT NOT NULL,
                events    TEXT NOT NULL DEFAULT '[]',
                result    TEXT NOT NULL DEFAULT '{}'
            )
        """)
        # Builds that were running when the process died will never transition —
        # mark them orphaned so the UI doesn't show a build spinning forever.
        conn.execute(
            "UPDATE builds SET status = 'orphaned' WHERE status = 'running'"
        )
        conn.commit()


def load_all() -> list[dict]:
    """
    Return all persisted builds as plain dicts, oldest first.
    Called once at startup to seed the in-memory _builds dict.
    """
    with _connect() as conn:
        rows = conn.execute(
            "SELECT id, spec_name, status, events, result FROM builds ORDER BY rowid ASC"
        ).fetchall()
    return [
        {
            "id": r["id"],
            "spec_name": r["spec_name"],
            "status": r["status"],
            "events": json.loads(r["events"]),
            "result": json.loads(r["result"]),
        }
        for r in rows
    ]


def save(build: dict) -> None:
    """
    Persist (or replace) a completed / failed / cancelled / orphaned build.
    Called from _run_build() once the async wrapper resolves.
    """
    with _connect() as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO builds (id, spec_name, status, events, result)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                build["id"],
                build["spec_name"],
                build["status"],
                json.dumps(build["events"]),
                json.dumps(build["result"]),
            ),
        )
        conn.commit()
