import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path(__file__).parent / "cache.db"


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    conn = get_connection()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS matches (
            match_id   TEXT PRIMARY KEY,
            puuid      TEXT NOT NULL,
            raw_json   TEXT NOT NULL,
            fetched_at TEXT NOT NULL
        )
        """
    )
    conn.commit()
    conn.close()


def get_cached_match(match_id: str) -> dict | None:
    conn = get_connection()
    row = conn.execute(
        "SELECT raw_json FROM matches WHERE match_id = ?", (match_id,)
    ).fetchone()
    conn.close()
    if row is None:
        return None
    return json.loads(row["raw_json"])


def save_match(match_id: str, puuid: str, match_data: dict) -> None:
    conn = get_connection()
    conn.execute(
        """
        INSERT OR IGNORE INTO matches (match_id, puuid, raw_json, fetched_at)
        VALUES (?, ?, ?, ?)
        """,
        (match_id, puuid, json.dumps(match_data), datetime.now(timezone.utc).isoformat()),
    )
    conn.commit()
    conn.close()
