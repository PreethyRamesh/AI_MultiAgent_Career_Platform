import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from .config import DATABASE_PATH

SCHEMA = """
CREATE TABLE IF NOT EXISTS progress_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    snapshot_date TEXT NOT NULL,
    xp INTEGER NOT NULL DEFAULT 0,
    level INTEGER NOT NULL DEFAULT 1,
    streak INTEGER NOT NULL DEFAULT 0,
    completion_pct REAL NOT NULL DEFAULT 0,
    hours_invested REAL NOT NULL DEFAULT 0,
    phase_progress REAL NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE(user_id, snapshot_date)
);

CREATE TABLE IF NOT EXISTS achievements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    achievement_key TEXT NOT NULL,
    name TEXT NOT NULL,
    description TEXT NOT NULL,
    icon TEXT NOT NULL,
    earned_at TEXT NOT NULL,
    UNIQUE(user_id, achievement_key)
);
"""

def _connect():
    path = Path(DATABASE_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with _connect() as conn:
        conn.executescript(SCHEMA)
        conn.commit()

def now():
    return datetime.now(timezone.utc).isoformat()

def upsert_snapshot(user_id, snapshot_date, xp, level, streak,
                    completion_pct, hours_invested, phase_progress):
    current = now()
    with _connect() as conn:
        conn.execute("""
            INSERT INTO progress_snapshots
            (user_id,snapshot_date,xp,level,streak,completion_pct,
             hours_invested,phase_progress,created_at,updated_at)
            VALUES (?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(user_id,snapshot_date) DO UPDATE SET
            xp=excluded.xp, level=excluded.level, streak=excluded.streak,
            completion_pct=excluded.completion_pct,
            hours_invested=excluded.hours_invested,
            phase_progress=excluded.phase_progress,
            updated_at=excluded.updated_at
        """, (user_id, snapshot_date, xp, level, streak, completion_pct,
              hours_invested, phase_progress, current, current))
        conn.commit()

def get_history(user_id, limit=90):
    with _connect() as conn:
        rows = conn.execute("""
            SELECT snapshot_date,xp,level,streak,completion_pct,
                   hours_invested,phase_progress
            FROM progress_snapshots
            WHERE user_id=?
            ORDER BY snapshot_date ASC LIMIT ?
        """, (user_id, limit)).fetchall()
        return [dict(row) for row in rows]

def achievement_exists(user_id, key):
    with _connect() as conn:
        return conn.execute(
            "SELECT 1 FROM achievements WHERE user_id=? AND achievement_key=?",
            (user_id, key)
        ).fetchone() is not None

def award_achievement(user_id, key, name, description, icon):
    if achievement_exists(user_id, key):
        return False
    with _connect() as conn:
        conn.execute("""
            INSERT INTO achievements
            (user_id,achievement_key,name,description,icon,earned_at)
            VALUES (?,?,?,?,?,?)
        """, (user_id, key, name, description, icon, now()))
        conn.commit()
    return True

def get_achievements(user_id):
    with _connect() as conn:
        rows = conn.execute("""
            SELECT achievement_key,name,description,icon,earned_at
            FROM achievements WHERE user_id=? ORDER BY earned_at ASC
        """, (user_id,)).fetchall()
        return [dict(row) for row in rows]
