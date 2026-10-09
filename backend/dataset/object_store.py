"""
AASI Phase 27 Large CFD Dataset & Provider-Agnostic Object Store.
Decouples metadata from large field files (VTK, mesh, U, p, k, omega, forceCoeffs, tarballs).
Enforces content-addressed storage (CAS): objects/sha256/ab/abcdef...
Universal vendor-agnostic interface:
- put_object()
- get_object()
- head_object()
- delete_object()
- exists()
- stream_object()
Enforces strict epistemic classification across 8 classes:
- REAL_EXECUTED_VERIFIED
- USER_EXECUTED_VERIFIED
- DATABASE_REAL
- SURROGATE
- ANALYTICAL
- SYNTHETIC_FIXTURE
- STAGED_ONLY
- NOT_EXECUTED
"""

from enum import Enum
from typing import Dict, Any, Optional, List, Union, BinaryIO, Generator
from pydantic import BaseModel, Field
from pathlib import Path
import hashlib
import json
import os
import io
from datetime import datetime, timezone
from abc import ABC, abstractmethod


class EpistemicClass(str, Enum):
    REAL_EXECUTED_VERIFIED = "REAL_EXECUTED_VERIFIED"
    USER_EXECUTED_VERIFIED = "USER_EXECUTED_VERIFIED"
    DATABASE_REAL = "DATABASE_REAL"
    SURROGATE = "SURROGATE"
    ANALYTICAL = "ANALYTICAL"
    SYNTHETIC_FIXTURE = "SYNTHETIC_FIXTURE"
    STAGED_ONLY = "STAGED_ONLY"
    NOT_EXECUTED = "NOT_EXECUTED"


class ProvenanceTaggedQuantity(BaseModel):
    """Every displayed numerical value carries full epistemic origin and lineage."""
    quantity_name: str
    value: float
    units: str = "dimensionless"
    source: EpistemicClass
    confidence: Optional[float] = None
    uncertainty: Optional[float] = None
    geometry: str
    reynolds: float
    mach: float = 0.15
    aoa_deg: float
    solver: str
    mesh_info: Dict[str, Any] = Field(default_factory=dict)
    provenance_hash: str
    verification_status: str


class ArtifactCategory(str, Enum):
    CASE_ARCHIVE = "CASE_ARCHIVE"
    MESH = "MESH"
    PRESSURE_FIELD = "PRESSURE_FIELD"
    VELOCITY_FIELD = "VELOCITY_FIELD"
    TURBULENCE_FIELD = "TURBULENCE_FIELD"
    FORCE_HISTORY = "FORCE_HISTORY"
    RESIDUAL_HISTORY = "RESIDUAL_HISTORY"
    VTK = "VTK"
    REPRODUCTION_BUNDLE = "REPRODUCTION_BUNDLE"
    METADATA = "METADATA"


class ObjectMetadata(BaseModel):
    object_id: str
    sha256: str
    size_bytes: int
    content_type: str = "application/octet-stream"
    epistemic_class: EpistemicClass = EpistemicClass.NOT_EXECUTED
    category: ArtifactCategory = ArtifactCategory.CASE_ARCHIVE
    custom_metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    storage_path: str = ""


class ArtifactDescriptor(BaseModel):
    artifact_id: str
    category: ArtifactCategory
    file_name: str
    size_bytes: int
    sha256: str
    epistemic_class: EpistemicClass
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    storage_uri: str


class ObjectStorageDriver(ABC):
    """Abstract driver for external or local object storage (Local, S3, R2, GCS)."""

    @abstractmethod
    def put_object(self, key: str, data: bytes, content_type: str = "application/octet-stream") -> int:
        pass

    @abstractmethod
    def get_object(self, key: str) -> Optional[bytes]:
        pass

    @abstractmethod
    def head_object(self, key: str) -> Optional[Dict[str, Any]]:
        pass

    @abstractmethod
    def delete_object(self, key: str) -> bool:
        pass

    @abstractmethod
    def exists(self, key: str) -> bool:
        pass

    @abstractmethod
    def stream_object(self, key: str, chunk_size: int = 65536) -> Generator[bytes, None, None]:
        pass


class LocalFilesystemDriver(ObjectStorageDriver):
    """Local filesystem driver with content-addressed sharding."""

    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _get_path(self, key: str) -> Path:
        # Standardize key path
        return self.base_dir / key

    def put_object(self, key: str, data: bytes, content_type: str = "application/octet-stream") -> int:
        path = self._get_path(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return len(data)

    def get_object(self, key: str) -> Optional[bytes]:
        path = self._get_path(key)
        if path.exists():
            return path.read_bytes()
        return None

    def head_object(self, key: str) -> Optional[Dict[str, Any]]:
        path = self._get_path(key)
        if not path.exists():
            return None
        stat = path.stat()
        return {
            "size_bytes": stat.st_size,
            "last_modified": stat.st_mtime,
        }

    def delete_object(self, key: str) -> bool:
        path = self._get_path(key)
        if path.exists():
            path.unlink()
            return True
        return False

    def exists(self, key: str) -> bool:
        return self._get_path(key).exists()

    def stream_object(self, key: str, chunk_size: int = 65536) -> Generator[bytes, None, None]:
        path = self._get_path(key)
        if not path.exists():
            return
        with open(path, "rb") as f:
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                yield chunk


class LargeObjectStore:
    """
    Provider-agnostic content-addressed storage engine.
    Stores large objects under: objects/sha256/{digest[:2]}/{digest}
    """

    def __init__(self, storage_root: Optional[Path] = None, driver: Optional[ObjectStorageDriver] = None):
        self.root = storage_root or Path("data/storage/large_objects")
        self.root.mkdir(parents=True, exist_ok=True)
        self.driver = driver or LocalFilesystemDriver(self.root)
        self.manifest_path = self.root / "object_registry.json"
        self._registry: Dict[str, Dict[str, Any]] = {}
        self._load_registry()

    def _load_registry(self):
        if self.manifest_path.exists():
            try:
                self._registry = json.loads(self.manifest_path.read_text(encoding="utf-8"))
            except Exception:
                self._registry = {}

    def _save_registry(self):
        self.manifest_path.write_text(json.dumps(self._registry, indent=2), encoding="utf-8")

    def _cas_key(self, digest: str) -> str:
        """Derive content-addressed storage key: objects/sha256/ab/abcdef..."""
        prefix = digest[:2].lower()
        return f"objects/sha256/{prefix}/{digest}"

    def put_object(
        self,
        content: Union[bytes, str],
        epistemic_class: EpistemicClass = EpistemicClass.NOT_EXECUTED,
        category: ArtifactCategory = ArtifactCategory.CASE_ARCHIVE,
        content_type: str = "application/octet-stream",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ObjectMetadata:
        """Store arbitrary binary content in content-addressed storage."""
        raw_bytes = content.encode("utf-8") if isinstance(content, str) else content
        digest = hashlib.sha256(raw_bytes).hexdigest()
        key = self._cas_key(digest)

        size = self.driver.put_object(key, raw_bytes, content_type)
        obj_id = f"OBJ-{digest[:16].upper()}"

        meta = ObjectMetadata(
            object_id=obj_id,
            sha256=digest,
            size_bytes=size,
            content_type=content_type,
            epistemic_class=epistemic_class,
            category=category,
            custom_metadata=metadata or {},
            storage_path=key,
        )

        self._registry[obj_id] = meta.model_dump()
        self._save_registry()
        return meta

    def get_object(self, object_id_or_hash: str) -> Optional[bytes]:
        """Retrieve binary content by object_id or sha256 digest."""
        meta = self.head_object(object_id_or_hash)
        if not meta:
            # Try interpreting as raw sha256
            if len(object_id_or_hash) == 64:
                key = self._cas_key(object_id_or_hash)
                return self.driver.get_object(key)
            return None
        return self.driver.get_object(meta.storage_path)

    def head_object(self, object_id_or_hash: str) -> Optional[ObjectMetadata]:
        """Inspect object metadata without loading entire binary into RAM."""
        if object_id_or_hash in self._registry:
            return ObjectMetadata.model_validate(self._registry[object_id_or_hash])
        for obj in self._registry.values():
            if obj["sha256"].lower() == object_id_or_hash.lower():
                return ObjectMetadata.model_validate(obj)
        return None

    def delete_object(self, object_id_or_hash: str) -> bool:
        meta = self.head_object(object_id_or_hash)
        if not meta:
            return False
        self.driver.delete_object(meta.storage_path)
        self._registry.pop(meta.object_id, None)
        self._save_registry()
        return True

    def exists(self, object_id_or_hash: str) -> bool:
        return self.head_object(object_id_or_hash) is not None

    def stream_object(self, object_id_or_hash: str, chunk_size: int = 65536) -> Generator[bytes, None, None]:
        meta = self.head_object(object_id_or_hash)
        if not meta:
            return
        yield from self.driver.stream_object(meta.storage_path, chunk_size)

    # Backwards-compatible methods for Phase 26
    def put_artifact(
        self,
        category: ArtifactCategory,
        file_name: str,
        content: Union[bytes, str],
        epistemic_class: EpistemicClass,
    ) -> ArtifactDescriptor:
        meta = self.put_object(
            content=content,
            epistemic_class=epistemic_class,
            category=category,
            metadata={"file_name": file_name},
        )
        return ArtifactDescriptor(
            artifact_id=meta.object_id,
            category=category,
            file_name=file_name,
            size_bytes=meta.size_bytes,
            sha256=meta.sha256,
            epistemic_class=epistemic_class,
            storage_uri=meta.storage_path,
        )

    def get_artifact_lazy(self, artifact_id: str) -> Optional[bytes]:
        return self.get_object(artifact_id)

    def list_artifacts(self, category: Optional[ArtifactCategory] = None) -> List[ArtifactDescriptor]:
        results = []
        for aid, data in self._registry.items():
            if category and data.get("category") != category.value:
                continue
            f_name = data.get("custom_metadata", {}).get("file_name", f"{aid}.bin")
            results.append(
                ArtifactDescriptor(
                    artifact_id=data["object_id"],
                    category=ArtifactCategory(data.get("category", ArtifactCategory.CASE_ARCHIVE)),
                    file_name=f_name,
                    size_bytes=data["size_bytes"],
                    sha256=data["sha256"],
                    epistemic_class=EpistemicClass(data.get("epistemic_class", EpistemicClass.NOT_EXECUTED)),
                    storage_uri=data["storage_path"],
                )
            )
        return results


# Global singleton object store
object_store = LargeObjectStore()
