"""
AASI Enterprise SQLite Investigation Database.
Provides structured relational indexing, full-text inquiry search,
polar queries, and analytics aggregation for enterprise workspaces.
"""

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


class InvestigationDatabase:
    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or Path("data/aasi_investigations.db")
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
                CREATE TABLE IF NOT EXISTS investigations (
                    job_id TEXT PRIMARY KEY,
                    investigation_id TEXT,
                    org_id TEXT DEFAULT 'default',
                    objective TEXT NOT NULL,
                    geometry TEXT NOT NULL,
                    alpha_deg REAL NOT NULL,
                    reynolds REAL NOT NULL,
                    mach REAL NOT NULL,
                    verification_status TEXT NOT NULL,
                    epistemic_class TEXT,
                    cl REAL,
                    cd REAL,
                    cm REAL,
                    provenance_hash TEXT,
                    tags TEXT DEFAULT '[]',
                    full_payload TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)

            # Auto-migrate if org_id column is missing in existing sqlite table
            cursor.execute("PRAGMA table_info(investigations)")
            cols = [row["name"] for row in cursor.fetchall()]
            if "org_id" not in cols:
                cursor.execute("ALTER TABLE investigations ADD COLUMN org_id TEXT DEFAULT 'default'")

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_investigations_org
                ON investigations(org_id)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_investigations_geom
                ON investigations(geometry)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_investigations_status
                ON investigations(verification_status)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_investigations_created
                ON investigations(created_at DESC)
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS enterprise_workspaces (
                    workspace_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    created_at TEXT NOT NULL
                )
            """)

            cursor.execute("""
                INSERT OR IGNORE INTO enterprise_workspaces (workspace_id, name, description, created_at)
                VALUES ('default', 'Mission Control Primary Workspace', 'Default aerospace aerodynamics investigation stream', datetime('now'))
            """)
            conn.commit()

    def upsert_investigation(
        self,
        job_id: str,
        investigation_id: str,
        objective: str,
        geometry: str,
        alpha_deg: float,
        reynolds: float,
        mach: float,
        verification_status: str,
        epistemic_class: Optional[str] = None,
        cl: Optional[float] = None,
        cd: Optional[float] = None,
        cm: Optional[float] = None,
        provenance_hash: Optional[str] = None,
        tags: Optional[List[str]] = None,
        full_payload: Optional[Dict[str, Any]] = None,
        org_id: str = "default",
    ) -> None:
        now = datetime.now(timezone.utc).isoformat()
        tags_json = json.dumps(tags or [])
        payload_json = json.dumps(full_payload or {}, default=str)

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO investigations (
                    job_id, investigation_id, org_id, objective, geometry, alpha_deg,
                    reynolds, mach, verification_status, epistemic_class,
                    cl, cd, cm, provenance_hash, tags, full_payload, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(job_id) DO UPDATE SET
                    org_id=coalesce(excluded.org_id, investigations.org_id),
                    verification_status=excluded.verification_status,
                    epistemic_class=excluded.epistemic_class,
                    cl=coalesce(excluded.cl, investigations.cl),
                    cd=coalesce(excluded.cd, investigations.cd),
                    cm=coalesce(excluded.cm, investigations.cm),
                    provenance_hash=coalesce(excluded.provenance_hash, investigations.provenance_hash),
                    full_payload=excluded.full_payload,
                    updated_at=excluded.updated_at
            """, (
                job_id,
                investigation_id,
                org_id,
                objective,
                geometry,
                alpha_deg,
                reynolds,
                mach,
                verification_status,
                epistemic_class,
                cl,
                cd,
                cm,
                provenance_hash,
                tags_json,
                payload_json,
                now,
                now,
            ))
            conn.commit()

    def get_investigation(self, job_id: str, org_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if org_id:
                cursor.execute("SELECT * FROM investigations WHERE job_id = ? AND org_id = ?", (job_id, org_id))
            else:
                cursor.execute("SELECT * FROM investigations WHERE job_id = ?", (job_id,))
            row = cursor.fetchone()
            if not row:
                return None
            res = dict(row)
            try:
                res["tags"] = json.loads(res["tags"])
            except Exception:
                res["tags"] = []
            try:
                res["full_payload"] = json.loads(res["full_payload"])
            except Exception:
                res["full_payload"] = {}
            return res

    def list_investigations(
        self,
        org_id: Optional[str] = None,
        query: Optional[str] = None,
        geometry: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        clauses = []
        params: List[Any] = []

        if org_id:
            clauses.append("org_id = ?")
            params.append(org_id)
        if query:
            clauses.append("(objective LIKE ? OR geometry LIKE ? OR job_id LIKE ?)")
            q = f"%{query}%"
            params.extend([q, q, q])
        if geometry:
            clauses.append("geometry = ?")
            params.append(geometry)
        if status:
            clauses.append("verification_status = ?")
            params.append(status)

        where_stmt = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        sql = f"SELECT * FROM investigations {where_stmt} ORDER BY created_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, params)
            rows = cursor.fetchall()
            results = []
            for r in rows:
                item = dict(r)
                try:
                    item["tags"] = json.loads(item["tags"])
                except Exception:
                    item["tags"] = []
                # omit massive full_payload in list queries for performance
                item.pop("full_payload", None)
                results.append(item)
            return results

    def get_analytics_summary(self, org_id: Optional[str] = None) -> Dict[str, Any]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            where_clause = "WHERE org_id = ?" if org_id else ""
            where_verified = "WHERE verification_status = 'VERIFIED'" + (" AND org_id = ?" if org_id else "")
            where_cl = "WHERE cl IS NOT NULL" + (" AND org_id = ?" if org_id else "")
            params = [org_id] if org_id else []

            cursor.execute(f"SELECT COUNT(*) as total FROM investigations {where_clause}", params)
            total = cursor.fetchone()["total"]

            cursor.execute(f"SELECT COUNT(*) as verified FROM investigations {where_verified}", params)
            verified = cursor.fetchone()["verified"]

            cursor.execute(f"SELECT COUNT(DISTINCT geometry) as airfoils FROM investigations {where_clause}", params)
            airfoils = cursor.fetchone()["airfoils"]

            cursor.execute(f"SELECT AVG(cl) as avg_cl, AVG(cd) as avg_cd FROM investigations {where_cl}", params)
            avg_row = cursor.fetchone()

            return {
                "total_investigations": total,
                "verified_investigations": verified,
                "unique_geometries": airfoils,
                "avg_cl": round(avg_row["avg_cl"] or 0.0, 4),
                "avg_cd": round(avg_row["avg_cd"] or 0.0, 4),
                "verification_rate_pct": round((verified / total * 100), 1) if total > 0 else 100.0,
                "org_id": org_id or "all",
            }


investigation_db = InvestigationDatabase()
