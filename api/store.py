"""
SQLite-backed build store.

Keeps completed and failed build records on disk so they survive server restarts.
Running builds are held in the in-memory _builds dict in main.py and persisted
here when they finish.

Schema versioning (4.6): schema_version table tracks applied migrations.
Indexes on status and created_at for efficient queries (4.6).
"""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

_DB_PATH = Path("builds.db")
_SCHEMA_VERSION = 2


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(str(_DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def _get_schema_version(conn: sqlite3.Connection) -> int:
    try:
        row = conn.execute("SELECT version FROM schema_version ORDER BY version DESC LIMIT 1").fetchone()
        return row["version"] if row else 0
    except sqlite3.OperationalError:
        return 0


def _apply_migrations(conn: sqlite3.Connection) -> None:
    version = _get_schema_version(conn)

    if version < 1:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS schema_version (
                version   INTEGER PRIMARY KEY,
                applied_at TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS builds (
                id         TEXT PRIMARY KEY,
                spec_name  TEXT NOT NULL,
                status     TEXT NOT NULL,
                events     TEXT NOT NULL DEFAULT '[]',
                result     TEXT NOT NULL DEFAULT '{}',
                created_at TEXT NOT NULL DEFAULT ''
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_builds_status ON builds(status)")
        conn.execute("INSERT INTO schema_version VALUES (1, ?)", (datetime.now(timezone.utc).isoformat(),))
        version = 1

    if version < 2:
        # Add created_at column if not present (migration for older databases)
        try:
            conn.execute("ALTER TABLE builds ADD COLUMN created_at TEXT NOT NULL DEFAULT ''")
        except sqlite3.OperationalError:
            pass  # column already exists
        conn.execute("CREATE INDEX IF NOT EXISTS idx_builds_created ON builds(created_at)")
        conn.execute("INSERT INTO schema_version VALUES (2, ?)", (datetime.now(timezone.utc).isoformat(),))

    conn.commit()


def init_db() -> None:
    """
    Create/migrate the builds table and mark orphaned running builds.
    """
    with _connect() as conn:
        _apply_migrations(conn)
        conn.execute("UPDATE builds SET status = 'orphaned' WHERE status = 'running'")
        conn.commit()


def load_all() -> list[dict]:
    """Return all persisted builds as plain dicts, oldest first."""
    with _connect() as conn:
        rows = conn.execute(
            "SELECT id, spec_name, status, events, result, created_at FROM builds ORDER BY rowid ASC"
        ).fetchall()
    return [
        {
            "id": r["id"],
            "spec_name": r["spec_name"],
            "status": r["status"],
            "events": json.loads(r["events"]),
            "result": json.loads(r["result"]),
            "created_at": r["created_at"],
        }
        for r in rows
    ]


def save(build: dict) -> None:
    """Persist (or replace) a completed / failed / cancelled / orphaned build."""
    with _connect() as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO builds (id, spec_name, status, events, result, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                build["id"],
                build["spec_name"],
                build["status"],
                json.dumps(build["events"]),
                json.dumps(build["result"]),
                build.get("created_at", datetime.now(timezone.utc).isoformat()),
            ),
        )
        conn.commit()
