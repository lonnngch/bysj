import sqlite3
from pathlib import Path
from typing import Dict, List, Optional


class EvaluationStore:
    def __init__(self, db_path: str) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS evaluations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    filename TEXT NOT NULL,
                    score REAL NOT NULL,
                    confidence REAL NOT NULL,
                    duration_sec REAL,
                    frame_count INTEGER,
                    engine TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.commit()

    def add(self, payload: Dict) -> int:
        with self._connect() as conn:
            cur = conn.execute(
                """
                INSERT INTO evaluations (
                    filename, score, confidence, duration_sec,
                    frame_count, engine, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    payload["filename"],
                    payload["score"],
                    payload["confidence"],
                    payload.get("duration_sec"),
                    payload.get("frame_count"),
                    payload["engine"],
                    payload["created_at"],
                ),
            )
            conn.commit()
            return int(cur.lastrowid)

    def list(self, limit: int = 20) -> List[Dict]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT id, filename, score, confidence, duration_sec,
                       frame_count, engine, created_at
                FROM evaluations
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
            return [dict(row) for row in rows]

    def get(self, item_id: int) -> Optional[Dict]:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT id, filename, score, confidence, duration_sec,
                       frame_count, engine, created_at
                FROM evaluations
                WHERE id = ?
                """,
                (item_id,),
            ).fetchone()
            return dict(row) if row else None
