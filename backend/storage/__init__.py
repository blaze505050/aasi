"""
AASI Phase 27 Storage Package.
Re-exports the large object store and CAS drivers.
"""

from backend.dataset.object_store import (
    LargeObjectStore,
    LocalFilesystemDriver,
    ObjectStorageDriver,
    ObjectMetadata,
    EpistemicClass,
    ArtifactCategory,
)

ContentAddressedObjectStore = LargeObjectStore
LocalFSObjectBackend = LocalFilesystemDriver

__all__ = [
    "LargeObjectStore",
    "LocalFilesystemDriver",
    "ContentAddressedObjectStore",
    "LocalFSObjectBackend",
    "ObjectStorageDriver",
    "ObjectMetadata",
    "EpistemicClass",
    "ArtifactCategory",
]
