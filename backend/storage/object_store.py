"""
AASI Phase 27 Content Addressed Object Store Adapter.
Universal wrapper supporting store(data) and retrieve(sha256).
"""

from typing import Optional, Union, Dict, Any
from pathlib import Path

from backend.dataset.object_store import (
    LargeObjectStore,
    LocalFilesystemDriver,
    ObjectMetadata,
    EpistemicClass,
    ArtifactCategory,
)


class LocalFSObjectBackend(LocalFilesystemDriver):
    def __init__(self, base_dir: Optional[str] = None):
        self.root = Path(base_dir) if base_dir else Path("data/storage")
        super().__init__(base_dir=self.root)


class ContentAddressedObjectStore(LargeObjectStore):
    def __init__(self, backend: Optional[LocalFilesystemDriver] = None, storage_root: Optional[Path] = None):
        root = storage_root or (getattr(backend, "root", None) or getattr(backend, "base_dir", None) or Path("data/storage/large_objects"))
        super().__init__(storage_root=root, driver=backend)

    def store(
        self,
        data: Union[bytes, str],
        content_type: str = "application/octet-stream",
        user_id: Optional[str] = None,
        epistemic_class: EpistemicClass = EpistemicClass.NOT_EXECUTED,
        **kwargs,
    ) -> ObjectMetadata:
        metadata = {"user_id": user_id} if user_id else {}
        metadata.update(kwargs)
        return self.put_object(
            content=data,
            content_type=content_type,
            epistemic_class=epistemic_class,
            metadata=metadata,
        )

    def retrieve(self, sha256: str) -> Optional[bytes]:
        return self.get_object(sha256)
