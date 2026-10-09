"""
AASI Commercial SQLite Database.
Persists organizations, projects, subscriptions, and usage events across restarts.
Ensures commercial data integrity, auditability, and quota enforcement.
"""

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from backend.auth.commercial import (
    Organization,
    Project,
    Plan,
    PlanTier,
    UsageEvent,
    UsageEventType,
    DEFAULT_PLANS,
    get_plan,
)


class CommercialDatabase:
    """SQLite-backed persistent store for AASI commercial state."""

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or Path("data/aasi_commercial.db")
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
        self._seed_default_org()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            # Organizations
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS organizations (
                    org_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    slug TEXT UNIQUE NOT NULL,
                    owner_id TEXT NOT NULL,
                    member_ids TEXT NOT NULL,
                    plan_id TEXT NOT NULL DEFAULT 'free',
                    created_at TEXT NOT NULL,
                    settings TEXT DEFAULT '{}',
                    is_active INTEGER DEFAULT 1
                )
            """)

            # Projects
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS projects (
                    project_id TEXT PRIMARY KEY,
                    org_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    description TEXT DEFAULT '',
                    member_ids TEXT NOT NULL,
                    investigation_ids TEXT DEFAULT '[]',
                    created_at TEXT NOT NULL,
                    is_active INTEGER DEFAULT 1,
                    FOREIGN KEY (org_id) REFERENCES organizations(org_id)
                )
            """)

            # Usage Events (metering ledger)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS usage_events (
                    event_id TEXT PRIMARY KEY,
                    org_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    project_id TEXT,
                    investigation_id TEXT,
                    event_type TEXT NOT NULL,
                    quantity REAL NOT NULL DEFAULT 1.0,
                    unit TEXT NOT NULL DEFAULT 'count',
                    timestamp TEXT NOT NULL,
                    metadata TEXT DEFAULT '{}'
                )
            """)

            cursor.execute("CREATE INDEX IF NOT EXISTS idx_usage_org_type_time ON usage_events(org_id, event_type, timestamp)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_projects_org ON projects(org_id)")
            conn.commit()

    def _seed_default_org(self) -> None:
        """Seed the default organization and project if not present."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT org_id FROM organizations WHERE org_id = 'default'")
            if not cursor.fetchone():
                cursor.execute("""
                    INSERT INTO organizations (org_id, name, slug, owner_id, member_ids, plan_id, created_at, settings, is_active)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1)
                """, (
                    "default",
                    "Orbit-1 Aerospace Engineering",
                    "orbit-1",
                    "usr_admin",
                    json.dumps(["usr_admin", "usr_chief_aero", "usr_auditor"]),
                    "professional",
                    datetime.now(timezone.utc).isoformat(),
                    json.dumps({}),
                ))

            cursor.execute("SELECT project_id FROM projects WHERE project_id = 'PRJ-DEFAULT'")
            if not cursor.fetchone():
                cursor.execute("""
                    INSERT INTO projects (project_id, org_id, name, description, member_ids, investigation_ids, created_at, is_active)
                    VALUES (?, ?, ?, ?, ?, ?, ?, 1)
                """, (
                    "PRJ-DEFAULT",
                    "default",
                    "Primary Aerodynamics Stream",
                    "Core aerodynamics validation and multi-fidelity investigations",
                    json.dumps(["usr_admin", "usr_chief_aero"]),
                    json.dumps([]),
                    datetime.now(timezone.utc).isoformat(),
                ))
            conn.commit()

    # ─── Organization CRUD ───

    def get_organization(self, org_id: str) -> Optional[Organization]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM organizations WHERE org_id = ? AND is_active = 1", (org_id,))
            row = cursor.fetchone()
            if not row:
                return None
            return Organization(
                org_id=row["org_id"],
                name=row["name"],
                slug=row["slug"],
                owner_id=row["owner_id"],
                member_ids=json.loads(row["member_ids"]),
                plan_id=row["plan_id"],
                created_at=row["created_at"],
                settings=json.loads(row["settings"] or "{}"),
                is_active=bool(row["is_active"]),
            )

    def get_organization_by_slug(self, slug: str) -> Optional[Organization]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM organizations WHERE slug = ? AND is_active = 1", (slug,))
            row = cursor.fetchone()
            if not row:
                return None
            return Organization(
                org_id=row["org_id"],
                name=row["name"],
                slug=row["slug"],
                owner_id=row["owner_id"],
                member_ids=json.loads(row["member_ids"]),
                plan_id=row["plan_id"],
                created_at=row["created_at"],
                settings=json.loads(row["settings"] or "{}"),
                is_active=bool(row["is_active"]),
            )

    def list_organizations(self) -> List[Organization]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM organizations WHERE is_active = 1 ORDER BY created_at ASC")
            orgs = []
            for row in cursor.fetchall():
                orgs.append(Organization(
                    org_id=row["org_id"],
                    name=row["name"],
                    slug=row["slug"],
                    owner_id=row["owner_id"],
                    member_ids=json.loads(row["member_ids"]),
                    plan_id=row["plan_id"],
                    created_at=row["created_at"],
                    settings=json.loads(row["settings"] or "{}"),
                    is_active=bool(row["is_active"]),
                ))
            return orgs

    def save_organization(self, org: Organization) -> None:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO organizations (org_id, name, slug, owner_id, member_ids, plan_id, created_at, settings, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(org_id) DO UPDATE SET
                    name = excluded.name,
                    slug = excluded.slug,
                    owner_id = excluded.owner_id,
                    member_ids = excluded.member_ids,
                    plan_id = excluded.plan_id,
                    settings = excluded.settings,
                    is_active = excluded.is_active
            """, (
                org.org_id,
                org.name,
                org.slug,
                org.owner_id,
                json.dumps(org.member_ids),
                org.plan_id,
                org.created_at,
                json.dumps(org.settings),
                1 if org.is_active else 0,
            ))
            conn.commit()

    def update_organization_plan(self, org_id: str, new_plan_id: str) -> bool:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE organizations SET plan_id = ? WHERE org_id = ?", (new_plan_id, org_id))
            conn.commit()
            return cursor.rowcount > 0

    # ─── Project CRUD ───

    def get_project(self, project_id: str) -> Optional[Project]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM projects WHERE project_id = ? AND is_active = 1", (project_id,))
            row = cursor.fetchone()
            if not row:
                return None
            return Project(
                project_id=row["project_id"],
                org_id=row["org_id"],
                name=row["name"],
                description=row["description"] or "",
                member_ids=json.loads(row["member_ids"]),
                investigation_ids=json.loads(row["investigation_ids"] or "[]"),
                created_at=row["created_at"],
                is_active=bool(row["is_active"]),
            )

    def list_projects_for_org(self, org_id: str) -> List[Project]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM projects WHERE org_id = ? AND is_active = 1 ORDER BY created_at ASC", (org_id,))
            projects = []
            for row in cursor.fetchall():
                projects.append(Project(
                    project_id=row["project_id"],
                    org_id=row["org_id"],
                    name=row["name"],
                    description=row["description"] or "",
                    member_ids=json.loads(row["member_ids"]),
                    investigation_ids=json.loads(row["investigation_ids"] or "[]"),
                    created_at=row["created_at"],
                    is_active=bool(row["is_active"]),
                ))
            return projects

    def save_project(self, project: Project) -> None:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO projects (project_id, org_id, name, description, member_ids, investigation_ids, created_at, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(project_id) DO UPDATE SET
                    name = excluded.name,
                    description = excluded.description,
                    member_ids = excluded.member_ids,
                    investigation_ids = excluded.investigation_ids,
                    is_active = excluded.is_active
            """, (
                project.project_id,
                project.org_id,
                project.name,
                project.description,
                json.dumps(project.member_ids),
                json.dumps(project.investigation_ids),
                project.created_at,
                1 if project.is_active else 0,
            ))
            conn.commit()

    # ─── Usage Events Metering ───

    def record_usage_event(self, event: UsageEvent) -> None:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO usage_events (event_id, org_id, user_id, project_id, investigation_id, event_type, quantity, unit, timestamp, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                event.event_id,
                event.org_id,
                event.user_id,
                event.project_id,
                event.investigation_id,
                event.event_type.value if hasattr(event.event_type, "value") else str(event.event_type),
                event.quantity,
                event.unit,
                event.timestamp,
                json.dumps(event.metadata or {}),
            ))
            conn.commit()

    def get_monthly_count(self, org_id: str, event_type: UsageEventType) -> int:
        now = datetime.now(timezone.utc)
        month_start_iso = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0).isoformat()
        evt_val = event_type.value if hasattr(event_type, "value") else str(event_type)

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COALESCE(SUM(quantity), 0) as total
                FROM usage_events
                WHERE org_id = ? AND event_type = ? AND timestamp >= ?
            """, (org_id, evt_val, month_start_iso))
            row = cursor.fetchone()
            return int(row["total"]) if row else 0

    def get_usage_summary(self, org_id: str) -> Dict[str, int]:
        now = datetime.now(timezone.utc)
        month_start_iso = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0).isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT event_type, COALESCE(SUM(quantity), 0) as total
                FROM usage_events
                WHERE org_id = ? AND timestamp >= ?
                GROUP BY event_type
            """, (org_id, month_start_iso))
            summary = {}
            for row in cursor.fetchall():
                summary[row["event_type"]] = int(row["total"])
            return summary

    def clear_usage_events(self, org_id: Optional[str] = None) -> None:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if org_id:
                cursor.execute("DELETE FROM usage_events WHERE org_id = ?", (org_id,))
            else:
                cursor.execute("DELETE FROM usage_events")
            conn.commit()


# Global singleton instance
commercial_db = CommercialDatabase()
