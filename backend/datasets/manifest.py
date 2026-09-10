"""
AASI Dataset Manifest Serializer & Verifier.

Generates and cryptographically verifies dataset manifests.
"""

import json
import hashlib
from typing import Dict, Any
from backend.datasets.models import DatasetManifest


class ManifestManager:
    """Handles JSON serialization and cryptographic verification of dataset manifests."""

    @classmethod
    def serialize(cls, manifest: DatasetManifest) -> str:
        """Serializes manifest to JSON."""
        return manifest.model_dump_json(indent=2)

    @classmethod
    def compute_manifest_hash(cls, manifest: DatasetManifest) -> str:
        """Generates SHA-256 hash of canonical manifest fields."""
        canonical = {
            "id": manifest.dataset_id,
            "version": manifest.version,
            "source": manifest.source,
            "checksum": manifest.checksum,
            "conditions": manifest.conditions,
            "variables": sorted(manifest.variables)
        }
        raw = json.dumps(canonical, sort_keys=True).encode("utf-8")
        return hashlib.sha256(raw).hexdigest()
