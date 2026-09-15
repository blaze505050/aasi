"""
AASI CFD Storage Architecture.
Decouples metadata, large field artifacts, and derived scientific features.
Supports provider-agnostic lazy loading of VTK, OpenFOAM fields, meshes, and archives.
"""

from typing import Dict, Any, Optional, BinaryIO
from pathlib import Path
import json
import hashlib
import os


class ObjectStorageBackend:
    """Provider-agnostic object storage interface with lazy retrieval."""

    def __init__(self, base_storage_dir: Optional[Path] = None):
        self.base_dir = base_storage_dir or Path("data/storage/artifacts")
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def put_artifact(self, artifact_key: str, data: bytes, content_type: str = "application/octet-stream") -> str:
        """Stores a binary artifact (VTK, tar.gz, mesh) and returns its SHA-256 hash."""
        digest = hashlib.sha256(data).hexdigest()
        target_path = self.base_dir / f"{digest}_{artifact_key}"
        target_path.write_bytes(data)
        return digest

    def get_artifact(self, digest: str, artifact_key: str) -> Optional[bytes]:
        """Lazy retrieval of binary artifact."""
        target_path = self.base_dir / f"{digest}_{artifact_key}"
        if target_path.exists():
            return target_path.read_bytes()
        return None

    def exists(self, digest: str, artifact_key: str) -> bool:
        target_path = self.base_dir / f"{digest}_{artifact_key}"
        return target_path.exists()


class MetadataStore:
    """Fast searchable metadata store for indexed CFD records."""

    def __init__(self, metadata_dir: Optional[Path] = None):
        self.metadata_dir = metadata_dir or Path("data/storage/metadata")
        self.metadata_dir.mkdir(parents=True, exist_ok=True)

    def save_record(self, record_id: str, record_data: Dict[str, Any]) -> None:
        path = self.metadata_dir / f"{record_id}.json"
        path.write_text(json.dumps(record_data, indent=2), encoding="utf-8")

    def load_record(self, record_id: str) -> Optional[Dict[str, Any]]:
        path = self.metadata_dir / f"{record_id}.json"
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
        return None

    def list_record_ids(self) -> list:
        return [f.stem for f in self.metadata_dir.glob("*.json")]


class ScientificFeatureStore:
    """Derived scientific feature store for instantaneous fast similarity search."""

    def __init__(self, feature_dir: Optional[Path] = None):
        self.feature_dir = feature_dir or Path("data/storage/features")
        self.feature_dir.mkdir(parents=True, exist_ok=True)
        self.index_file = self.feature_dir / "feature_index.json"
        self._index: Dict[str, Dict[str, float]] = {}
        self._load()

    def _load(self):
        if self.index_file.exists():
            try:
                self._index = json.loads(self.index_file.read_text(encoding="utf-8"))
            except Exception:
                self._index = {}

    def save_features(self, record_id: str, features: Dict[str, float]):
        self._index[record_id] = features
        self.index_file.write_text(json.dumps(self._index, indent=2), encoding="utf-8")

    def get_all_features(self) -> Dict[str, Dict[str, float]]:
        return self._index
