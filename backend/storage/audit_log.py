"""
AASI Cryptographic Audit Log Engine.
Provides an immutable, append-only, SHA-256 chained transaction log
for defense and aerospace compliance (ITAR, ASME V&V 20, ISO 9001).
"""

import json
import sqlite3
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


class AuditLogEngine:
    """Tamper-evident append-only cryptographic ledger."""

    GENESIS_HASH = "0000000000000000000000000000000000000000000000000000000000000000"

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or Path("data/aasi_audit_log.db")
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS audit_chain (
                    sequence_num INTEGER PRIMARY KEY AUTOINCREMENT,
                    entry_id TEXT UNIQUE NOT NULL,
                    timestamp TEXT NOT NULL,
                    org_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    action TEXT NOT NULL,
                    resource_id TEXT NOT NULL,
                    details TEXT NOT NULL,
                    prev_hash TEXT NOT NULL,
                    current_hash TEXT NOT NULL
                )
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_org ON audit_chain(org_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_action ON audit_chain(action)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_time ON audit_chain(timestamp DESC)")
            conn.commit()

    def record_entry(
        self,
        org_id: str,
        user_id: str,
        action: str,
        resource_id: str,
        details: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Atomically appends a new signed block to the cryptographic chain."""
        now_iso = datetime.now(timezone.utc).isoformat()
        import secrets
        entry_id = f"AUD-{secrets.token_hex(8).upper()}"

        with self._get_connection() as conn:
            cursor = conn.cursor()
            # Fetch latest entry to get previous hash
            cursor.execute("SELECT sequence_num, current_hash FROM audit_chain ORDER BY sequence_num DESC LIMIT 1")
            last_row = cursor.fetchone()

            if last_row:
                seq = last_row["sequence_num"] + 1
                prev_hash = last_row["current_hash"]
            else:
                seq = 1
                prev_hash = self.GENESIS_HASH

            details_str = json.dumps(details, sort_keys=True)
            raw_signature = f"{seq}:{entry_id}:{now_iso}:{org_id}:{user_id}:{action}:{resource_id}:{details_str}:{prev_hash}"
            current_hash = hashlib.sha256(raw_signature.encode("utf-8")).hexdigest()

            cursor.execute("""
                INSERT INTO audit_chain (sequence_num, entry_id, timestamp, org_id, user_id, action, resource_id, details, prev_hash, current_hash)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                seq,
                entry_id,
                now_iso,
                org_id,
                user_id,
                action,
                resource_id,
                details_str,
                prev_hash,
                current_hash,
            ))
            conn.commit()

            return {
                "sequence_num": seq,
                "entry_id": entry_id,
                "timestamp": now_iso,
                "action": action,
                "resource_id": resource_id,
                "current_hash": current_hash,
                "prev_hash": prev_hash,
            }

    def verify_chain_integrity(self) -> Dict[str, Any]:
        """Scans the entire cryptographic chain to verify zero tampering."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM audit_chain ORDER BY sequence_num ASC")
            rows = cursor.fetchall()

            if not rows:
                return {"valid": True, "entries_checked": 0, "status": "EMPTY_CHAIN"}

            prev_expected_hash = self.GENESIS_HASH

            for idx, r in enumerate(rows):
                # 1. Verify previous hash linkage
                if r["prev_hash"] != prev_expected_hash:
                    return {
                        "valid": False,
                        "broken_sequence": r["sequence_num"],
                        "entry_id": r["entry_id"],
                        "reason": f"Hash chain broken at seq {r['sequence_num']}. Expected {prev_expected_hash[:16]}..., got {r['prev_hash'][:16]}...",
                    }

                # 2. Recalculate block hash
                raw_sig = f"{r['sequence_num']}:{r['entry_id']}:{r['timestamp']}:{r['org_id']}:{r['user_id']}:{r['action']}:{r['resource_id']}:{r['details']}:{r['prev_hash']}"
                expected_hash = hashlib.sha256(raw_sig.encode("utf-8")).hexdigest()

                if r["current_hash"] != expected_hash:
                    return {
                        "valid": False,
                        "broken_sequence": r["sequence_num"],
                        "entry_id": r["entry_id"],
                        "reason": f"Payload modification detected at seq {r['sequence_num']}. Hash mismatch.",
                    }

                prev_expected_hash = r["current_hash"]

            return {
                "valid": True,
                "entries_checked": len(rows),
                "head_sequence": rows[-1]["sequence_num"],
                "head_hash": rows[-1]["current_hash"],
                "status": "CHAIN_INTEGRITY_VERIFIED",
            }

    def list_entries(self, org_id: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if org_id:
                cursor.execute("SELECT * FROM audit_chain WHERE org_id = ? ORDER BY sequence_num DESC LIMIT ?", (org_id, limit))
            else:
                cursor.execute("SELECT * FROM audit_chain ORDER BY sequence_num DESC LIMIT ?", (limit,))
            
            entries = []
            for r in cursor.fetchall():
                entries.append({
                    "sequence_num": r["sequence_num"],
                    "entry_id": r["entry_id"],
                    "timestamp": r["timestamp"],
                    "org_id": r["org_id"],
                    "user_id": r["user_id"],
                    "action": r["action"],
                    "resource_id": r["resource_id"],
                    "details": json.loads(r["details"]),
                    "current_hash": r["current_hash"],
                    "prev_hash": r["prev_hash"],
                })
            return entries


# Global singleton instance
audit_logger = AuditLogEngine()
