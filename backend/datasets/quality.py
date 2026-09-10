"""
AASI Dataset Quality & Deduplication Engine.

Provides deduplication, noise filtering, and canonical unit normalization.
"""

from typing import List, Dict, Any, Tuple


class QualityManager:
    """Manages quality filters, deduplication, and normalization."""

    @classmethod
    def deduplicate(cls, samples: List[Dict[str, Any]], key_fields: List[str]) -> Tuple[List[Dict[str, Any]], int]:
        """Removes duplicate rows based on key fields (e.g. geometry, mach, reynolds, aoa)."""
        seen = set()
        deduped = []
        duplicates_removed = 0

        for s in samples:
            key = tuple(s.get(k) for k in key_fields)
            if key in seen:
                duplicates_removed += 1
            else:
                seen.add(key)
                deduped.append(s)

        return deduped, duplicates_removed

    @classmethod
    def normalize_units(cls, sample: Dict[str, Any]) -> Dict[str, Any]:
        """Normalizes condition fields to standard SI units."""
        norm = dict(sample)
        # Convert angle of attack from radians to degrees if labeled rad
        if "aoa_rad" in norm and "aoa_deg" not in norm:
            import math
            norm["aoa_deg"] = math.degrees(float(norm["aoa_rad"]))
        return norm
