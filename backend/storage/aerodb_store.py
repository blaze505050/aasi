"""
AASI Aerodynamic Database (AeroDB) Persistent SQLite Storage.

Provides ACID persistence for multi-condition aerodynamic sweeps, stability derivatives,
and polar curves so user work survives backend restarts.
"""

import json
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone


class AeroDatabaseStore:
    """
    SQLite persistence layer for AeroDatabase instances.
    Ensures polar sweeps and stability matrices are preserved across restarts.
    """

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or Path("data/aasi_aerodb.db")
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS aerodatabases (
                    db_id TEXT PRIMARY KEY,
                    geometry_name TEXT NOT NULL,
                    created_at_utc TEXT NOT NULL,
                    chord_m REAL NOT NULL,
                    provenance_hash TEXT NOT NULL,
                    polar_count INTEGER NOT NULL,
                    total_points INTEGER NOT NULL,
                    full_payload TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_aerodb_geometry
                ON aerodatabases(geometry_name)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_aerodb_created
                ON aerodatabases(created_at_utc)
            """)
            conn.commit()

    def save(self, db_dict: Dict[str, Any]) -> bool:
        """Persists an AeroDatabase serialized dictionary."""
        db_id = db_dict.get("db_id")
        if not db_id:
            return False

        geometry_name = db_dict.get("geometry_name", "UNKNOWN")
        created_at = db_dict.get("created_at_utc", datetime.now(timezone.utc).isoformat())
        chord_m = float(db_dict.get("chord_m", 1.0))
        provenance_hash = db_dict.get("provenance_hash", "")
        polars = db_dict.get("polars", [])
        polar_count = len(polars)
        total_points = sum(len(p.get("points", [])) for p in polars)
        payload_json = json.dumps(db_dict)
        now_iso = datetime.now(timezone.utc).isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO aerodatabases (
                    db_id, geometry_name, created_at_utc, chord_m,
                    provenance_hash, polar_count, total_points,
                    full_payload, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                db_id, geometry_name, created_at, chord_m,
                provenance_hash, polar_count, total_points,
                payload_json, now_iso
            ))
            conn.commit()
        return True

    def get(self, db_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves an AeroDatabase dictionary by id."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT full_payload FROM aerodatabases WHERE db_id = ?", (db_id,))
            row = cursor.fetchone()
            if row:
                return json.loads(row["full_payload"])
        return None

    def list_all(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Lists metadata summaries for stored databases."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT db_id, geometry_name, created_at_utc, chord_m,
                       provenance_hash, polar_count, total_points
                FROM aerodatabases
                ORDER BY created_at_utc DESC
                LIMIT ?
            """, (limit,))
            rows = cursor.fetchall()
            return [dict(r) for r in rows]

    def delete(self, db_id: str) -> bool:
        """Deletes a database by id."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM aerodatabases WHERE db_id = ?", (db_id,))
            conn.commit()
            return cursor.rowcount > 0


# Default global store instance
aerodb_store = AeroDatabaseStore()
