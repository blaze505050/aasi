"""
AASI 2.0 Runtime Governor — Cryptographic Audit Log.
"""

from typing import List, Dict, Any
from backend.governor.safety_governor import global_governor


class AuditLogViewer:
    """Provides structured query access to the governor's tamper-evident audit trail."""

    @classmethod
    def get_entries(cls, limit: int = 100) -> List[Dict[str, Any]]:
        return global_governor.get_audit_log(limit=limit)

    @classmethod
    def verify_integrity(cls) -> bool:
        return global_governor.verify_audit_log()
