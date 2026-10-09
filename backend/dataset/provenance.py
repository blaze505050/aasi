"""
AASI Dataset Cryptographic Provenance and Ingestion Guard.
Verifies Merkle provenance roots and guards against path traversal in dataset archives.
"""

from typing import Dict, Any, List, Optional
import hashlib
import json
from pathlib import Path


class DatasetProvenanceGuard:
    """Verifies cryptographic digests and enforces security bounds on dataset ingestion."""

    @classmethod
    def compute_record_merkle_root(cls, record_dict: Dict[str, Any]) -> str:
        """
        Constructs a deterministic Merkle hash tree over dataset record attributes.
        """
        components = [
            f"geom:{record_dict.get('geometry', {}).get('geometry_id', '')}",
            f"flow:{record_dict.get('flow', {}).get('reynolds', 0)}_{record_dict.get('flow', {}).get('aoa_deg', 0)}",
            f"mesh:{record_dict.get('mesh', {}).get('cell_count', 0)}",
            f"solver:{record_dict.get('solver', {}).get('solver', '')}",
            f"results:{record_dict.get('results', {}).get('cl', 0)}_{record_dict.get('results', {}).get('cd', 0)}",
        ]

        # Leaf hashes
        leaves = [hashlib.sha256(c.encode("utf-8")).hexdigest() for c in components]

        # Pairwise Merkle reduction
        current_layer = leaves
        while len(current_layer) > 1:
            next_layer = []
            for i in range(0, len(current_layer), 2):
                left = current_layer[i]
                right = current_layer[i + 1] if i + 1 < len(current_layer) else left
                combined = hashlib.sha256((left + right).encode("utf-8")).hexdigest()
                next_layer.append(combined)
            current_layer = next_layer

        return current_layer[0]

    @classmethod
    def validate_archive_path_safety(cls, file_names: Any) -> bool:
        """
        Prevents path traversal attacks ('../' or absolute paths) in dataset tarballs.
        """
        if hasattr(file_names, "getnames"):
            names = file_names.getnames()
        elif hasattr(file_names, "getmembers"):
            names = [m.name for m in file_names.getmembers()]
        else:
            names = [m.name if hasattr(m, "name") else str(m) for m in file_names]

        for name in names:
            if ".." in name or name.startswith("/") or name.startswith("\\"):
                return False
            # Check for Windows absolute path drive letters like C:
            if len(name) >= 2 and name[1] == ":":
                return False
        return True

