"""
Unit and Integration Tests for Milestone 7: Scientific Memory Engine.
Governing Doctrine: Absolute Anti-Fabrication Rule.
Section 9 of Architecture & Prompt 8:
- Multi-dimensional similarity retrieval over geometry, Re, Mach, AoA, solver, and target quantity.
- Epistemic Trust Priority: Verified CFD and empirical data strictly outrank model-generated text.
- Negative evidence: Failed investigations remain searchable with failure diagnosis.
- Cryptographic provenance and Merkle hashes.
- REST API routes in backend/api/routes_memory.py.
"""

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.science.memory import (
    EpistemicTrustTier,
    MemoryEntryType,
    MemoryQuery,
    MemorySearchResult,
    ScientificMemoryEngine,
    ScientificMemoryEntry,
    get_trust_weight,
    scientific_memory,
)


@pytest.fixture
def client():
    return TestClient(app)


# ---------------------------------------------------------------------------
# 1. Hydration and Ledger Integration
# ---------------------------------------------------------------------------

def test_memory_hydrated_from_ledger():
    """Verify memory has loaded existing verified and failed entries from empirical_ledger.json."""
    stats = scientific_memory.get_stats()
    assert stats["total_entries"] >= 4
    assert stats["verified_results_count"] >= 3
    assert stats["failed_investigations_count"] >= 1


def test_entry_provenance_hashing():
    """Verify cryptographic SHA-256 hash sealing for memory entries."""
    entry = ScientificMemoryEntry(
        memory_id="MEM-TEST-001",
        entry_type=MemoryEntryType.VERIFIED_RESULT,
        trust_tier=EpistemicTrustTier.VERIFIED_CFD,
        geometry="NACA 0012",
        operating_conditions={"alpha_deg": 4.0, "reynolds": 3.0e6, "mach": 0.15},
        solver="simpleFoam",
        target_quantities=["CL", "CD"],
        results={"CL": 0.441, "CD": 0.0084},
    )
    digest = entry.compute_provenance_hash()
    assert len(digest) == 64
    assert entry.provenance_hash == digest


# ---------------------------------------------------------------------------
# 2. Multi-Dimensional Similarity Scoring
# ---------------------------------------------------------------------------

def test_geometry_similarity_scoring():
    """Verify geometry similarity gives 1.0 for exact, ~0.85 for series match, lower for distant."""
    entry = ScientificMemoryEntry(
        memory_id="MEM-GEOM-1",
        entry_type=MemoryEntryType.VERIFIED_RESULT,
        trust_tier=EpistemicTrustTier.VERIFIED_CFD,
        geometry="NACA 0012",
        operating_conditions={"alpha_deg": 4.0, "reynolds": 3.0e6, "mach": 0.15},
    )

    # Exact match
    q_exact = MemoryQuery(geometry="NACA 0012")
    score_exact, dims_exact = scientific_memory.compute_similarity(q_exact, entry)
    assert dims_exact["geometry"] == 1.0

    # Series match (NACA 0015 vs NACA 0012)
    q_series = MemoryQuery(geometry="NACA 0015")
    score_series, dims_series = scientific_memory.compute_similarity(q_series, entry)
    assert dims_series["geometry"] == 0.85

    # Completely different
    q_diff = MemoryQuery(geometry="SUPERCRITICAL_SC0414")
    score_diff, dims_diff = scientific_memory.compute_similarity(q_diff, entry)
    assert dims_diff["geometry"] < 0.50


def test_reynolds_log_similarity():
    """Verify Reynolds similarity is computed in log10 space."""
    entry = ScientificMemoryEntry(
        memory_id="MEM-RE-1",
        entry_type=MemoryEntryType.VERIFIED_RESULT,
        trust_tier=EpistemicTrustTier.VERIFIED_CFD,
        geometry="NACA 0012",
        operating_conditions={"reynolds": 1.0e6, "alpha_deg": 0.0, "mach": 0.1},
    )

    # Identical Re
    q_ident = MemoryQuery(reynolds=1.0e6)
    _, dims_ident = scientific_memory.compute_similarity(q_ident, entry)
    assert dims_ident["reynolds"] == 1.0

    # 1 order of magnitude difference (1e6 vs 1e7) -> 1 - (1.0 / 2.0) = 0.5
    q_1_order = MemoryQuery(reynolds=1.0e7)
    _, dims_1_order = scientific_memory.compute_similarity(q_1_order, entry)
    assert pytest.approx(dims_1_order["reynolds"], abs=1e-2) == 0.50

    # 2 orders of magnitude difference (1e6 vs 1e8) -> 1 - (2.0 / 2.0) = 0.0
    q_2_order = MemoryQuery(reynolds=1.0e8)
    _, dims_2_order = scientific_memory.compute_similarity(q_2_order, entry)
    assert dims_2_order["reynolds"] == 0.0


def test_aoa_proximity_scoring():
    """Verify AoA proximity scales linearly with angle difference."""
    entry = ScientificMemoryEntry(
        memory_id="MEM-AOA-1",
        entry_type=MemoryEntryType.VERIFIED_RESULT,
        trust_tier=EpistemicTrustTier.VERIFIED_CFD,
        geometry="NACA 0012",
        operating_conditions={"alpha_deg": 4.0},
    )

    # Exact AoA
    _, dims_exact = scientific_memory.compute_similarity(MemoryQuery(alpha_deg=4.0), entry)
    assert dims_exact["alpha"] == 1.0

    # 2 degrees away -> 1 - (2 / 10) = 0.8
    _, dims_2deg = scientific_memory.compute_similarity(MemoryQuery(alpha_deg=6.0), entry)
    assert pytest.approx(dims_2deg["alpha"], abs=1e-2) == 0.80

    # 10 degrees away -> 0.0
    _, dims_10deg = scientific_memory.compute_similarity(MemoryQuery(alpha_deg=14.0), entry)
    assert dims_10deg["alpha"] == 0.0


# ---------------------------------------------------------------------------
# 3. Epistemic Trust Priority Rule
# ---------------------------------------------------------------------------

def test_verified_evidence_strictly_outranks_model_generated():
    """
    CRITICAL RULE: Verified CFD evidence (trust weight 1.0) strictly outranks
    model-generated text (trust weight 0.20) even if both have similar geometric/flow conditions.
    """
    custom_engine = ScientificMemoryEngine.__new__(ScientificMemoryEngine)
    custom_engine._entries = {}

    # Entry 1: Model-generated claim with exact geometry match
    entry_model = ScientificMemoryEntry(
        memory_id="MEM-MODEL-GEN",
        entry_type=MemoryEntryType.SCIENTIFIC_ASSUMPTION,
        trust_tier=EpistemicTrustTier.MODEL_GENERATED,
        geometry="NACA 0012",
        operating_conditions={"alpha_deg": 4.0, "reynolds": 3.0e6, "mach": 0.15},
        results={"CL": 0.440},
    )
    custom_engine._entries[entry_model.memory_id] = entry_model

    # Entry 2: Verified CFD with near-match geometry
    entry_verified = ScientificMemoryEntry(
        memory_id="MEM-CFD-VERIFIED",
        entry_type=MemoryEntryType.VERIFIED_RESULT,
        trust_tier=EpistemicTrustTier.VERIFIED_CFD,
        geometry="NACA 0012",
        operating_conditions={"alpha_deg": 4.0, "reynolds": 3.0e6, "mach": 0.15},
        results={"CL": 0.441, "CD": 0.0084},
    )
    custom_engine._entries[entry_verified.memory_id] = entry_verified

    query = MemoryQuery(geometry="NACA 0012", alpha_deg=4.0, reynolds=3.0e6, apply_trust_weight=True)
    results = custom_engine.search(query)

    assert len(results) == 2
    # Verified CFD must be the top result
    assert results[0].entry.memory_id == "MEM-CFD-VERIFIED"
    assert results[0].trust_weight == 1.0
    assert results[0].effective_score > results[1].effective_score
    # Model-generated entry is ranked second
    assert results[1].entry.memory_id == "MEM-MODEL-GEN"
    assert results[1].trust_weight == 0.20


# ---------------------------------------------------------------------------
# 4. Negative Evidence (Failure Preservation)
# ---------------------------------------------------------------------------

def test_negative_evidence_searchable():
    """Verify failed investigations are retained and retrievable as negative evidence."""
    failures = scientific_memory.get_failures()
    assert len(failures) >= 1
    failed_naca4412 = [f for f in failures if "4412" in f.geometry]
    assert len(failed_naca4412) >= 1
    failure = failed_naca4412[0]
    assert failure.entry_type == MemoryEntryType.FAILED_INVESTIGATION
    assert len(failure.failures) > 0
    assert failure.failures[0]["diagnosis"] == "COURANT_INSTABILITY"


# ---------------------------------------------------------------------------
# 5. REST API Routes
# ---------------------------------------------------------------------------

def test_api_memory_stats(client):
    """GET /api/memory/stats returns overview of memory corpus."""
    resp = client.get("/api/memory/stats")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_entries"] >= 4
    assert data["verified_results_count"] >= 3
    assert data["failed_investigations_count"] >= 1


def test_api_trust_tiers(client):
    """GET /api/memory/trust-tiers lists trust tiers and weights."""
    resp = client.get("/api/memory/trust-tiers")
    assert resp.status_code == 200
    tiers = resp.json()
    assert tiers["VERIFIED_CFD"]["weight"] == 1.0
    assert tiers["MODEL_GENERATED"]["weight"] == 0.20
    assert tiers["VERIFIED_CFD"]["weight"] > tiers["MODEL_GENERATED"]["weight"]


def test_api_memory_failures(client):
    """GET /api/memory/failures retrieves negative evidence."""
    resp = client.get("/api/memory/failures")
    assert resp.status_code == 200
    failures = resp.json()
    assert len(failures) >= 1
    assert any("4412" in f["geometry"] for f in failures)


def test_api_memory_query(client):
    """POST /api/memory/query performs similarity retrieval."""
    payload = {
        "geometry": "NACA 0012",
        "alpha_deg": 4.0,
        "reynolds": 3000000.0,
        "mach": 0.15,
        "target_quantity": "CL",
        "apply_trust_weight": True,
        "limit": 5,
    }
    resp = client.post("/api/memory/query", json=payload)
    assert resp.status_code == 200
    results = resp.json()
    assert len(results) > 0
    top = results[0]
    assert top["similarity_score"] > 0.8
    assert top["entry"]["geometry"] == "NACA 0012"
    assert "CL" in top["entry"]["results"]


def test_api_memory_entry_crud(client):
    """POST /api/memory/entries and GET /api/memory/entries/{id}."""
    entry_payload = {
        "memory_id": "MEM-API-TEST-99",
        "entry_type": "VERIFIED_RESULT",
        "trust_tier": "EXPERIMENTAL",
        "geometry": "RAE 2822",
        "operating_conditions": {"alpha_deg": 2.79, "reynolds": 6.5e6, "mach": 0.725},
        "solver": "Transonic Tunnel",
        "target_quantities": ["CL", "CD"],
        "results": {"CL": 0.743, "CD": 0.0127},
        "assumptions": ["Transonic shock boundary layer interaction test"],
    }
    post_resp = client.post("/api/memory/entries", json=entry_payload)
    assert post_resp.status_code == 200
    created = post_resp.json()
    assert created["memory_id"] == "MEM-API-TEST-99"
    assert created["provenance_hash"] != ""

    get_resp = client.get("/api/memory/entries/MEM-API-TEST-99")
    assert get_resp.status_code == 200
    fetched = get_resp.json()
    assert fetched["geometry"] == "RAE 2822"
    assert fetched["provenance_hash"] == created["provenance_hash"]
