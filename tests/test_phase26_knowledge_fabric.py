"""
AASI Phase 26 Knowledge Fabric & Object Storage Test Suite.
Verifies provider-agnostic object store, lazy retrieval, and the 8 epistemic classes.
"""

import pytest
from backend.dataset.object_store import (
    LargeObjectStore,
    EpistemicClass,
    ArtifactCategory,
    ProvenanceTaggedQuantity,
)


def test_epistemic_classes_exhaustive_and_distinct():
    """Verify all 8 epistemic classes are distinct and uncollapsed."""
    classes = [
        EpistemicClass.REAL_EXECUTED_VERIFIED,
        EpistemicClass.USER_EXECUTED_VERIFIED,
        EpistemicClass.DATABASE_REAL,
        EpistemicClass.SURROGATE,
        EpistemicClass.ANALYTICAL,
        EpistemicClass.SYNTHETIC_FIXTURE,
        EpistemicClass.STAGED_ONLY,
        EpistemicClass.NOT_EXECUTED,
    ]
    vals = [c.value for c in classes]
    assert len(vals) == 8
    assert len(vals) == len(set(vals))


def test_object_store_put_and_lazy_get(tmp_path):
    """Verify storing artifacts and lazy retrieval of binary fields."""
    store = LargeObjectStore(storage_root=tmp_path / "large_objects")

    test_content = b"OpenFOAM-10 mesh points and cell faces binary data"
    desc = store.put_artifact(
        category=ArtifactCategory.MESH,
        file_name="polyMesh.tar.gz",
        content=test_content,
        epistemic_class=EpistemicClass.REAL_EXECUTED_VERIFIED,
    )

    assert desc.artifact_id.startswith("OBJ-")
    assert desc.size_bytes == len(test_content)
    assert desc.epistemic_class == EpistemicClass.REAL_EXECUTED_VERIFIED

    # Retrieve lazily
    retrieved = store.get_artifact_lazy(desc.artifact_id)
    assert retrieved == test_content

    # List
    mesh_artifacts = store.list_artifacts(category=ArtifactCategory.MESH)
    assert len(mesh_artifacts) == 1
    assert mesh_artifacts[0].file_name == "polyMesh.tar.gz"


def test_provenance_tagged_quantity_model():
    """Verify every numerical value carries complete provenance and epistemic origin."""
    qty = ProvenanceTaggedQuantity(
        quantity_name="CL",
        value=1.0820,
        source=EpistemicClass.REAL_EXECUTED_VERIFIED,
        confidence=0.99,
        uncertainty=0.008,
        geometry="NACA 4412",
        reynolds=3e6,
        mach=0.15,
        aoa_deg=6.0,
        solver="simpleFoam",
        mesh_info={"cell_count": 48000, "y_plus": 0.85},
        provenance_hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        verification_status="RESULTS_VERIFIED",
    )

    assert qty.value == 1.0820
    assert qty.source == EpistemicClass.REAL_EXECUTED_VERIFIED
    assert qty.verification_status == "RESULTS_VERIFIED"
    assert len(qty.provenance_hash) == 64
