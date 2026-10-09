"""
AASI Phase 4: Consolidated Epistemic Memory & Merkle Lineage API Router.
Governing Doctrine: Absolute Anti-Fabrication Rule.

Endpoints for:
- Multi-dimensional similarity retrieval across geometry, Re, Mach, and alpha
- Prior-knowledge warm-start synthesis for sweeps and optimization loops
- Cryptographic Merkle-DAG experiment lineage inspection and audit proofs
- Preserved negative evidence (failure modes and repair strategies)
- Unified epistemic trust ranking
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from backend.science.memory import (
    EpistemicTrustTier as LegacyTrustTier,
    MemoryEntryType,
    MemoryQuery,
    MemorySearchResult,
    ScientificMemoryEntry,
    get_trust_weight as legacy_get_trust_weight,
    scientific_memory,
)
from backend.science.epistemic_kernel import (
    EpistemicMemoryKernel,
    EpistemicQuery,
    EpistemicRecord,
    EpistemicSearchResult,
    EpistemicTrustTier,
    WarmStartProposal,
    epistemic_kernel,
    get_trust_weight,
)
from backend.science.merkle_lineage import (
    MerkleLineageGraph,
    MerkleLineageNode,
    merkle_lineage,
)

router = APIRouter(prefix="/memory", tags=["Scientific Memory"])


# ────────────────────────────────────────────────────────────────
# 1. Similarity Retrieval & Records
# ────────────────────────────────────────────────────────────────

@router.post("/query", response_model=List[MemorySearchResult], summary="Multi-Dimensional Similarity Retrieval")
async def query_scientific_memory(query: MemoryQuery) -> List[MemorySearchResult]:
    """
    Retrieves stored scientific memories matching query parameters across
    geometry, Reynolds number (log10), Mach number, angle of attack, and target quantities.
    Enforces strict Epistemic Trust: Verified CFD/empirical evidence strictly prioritizes
    over model-generated text or unverified assertions.
    """
    return scientific_memory.search(query)


@router.post("/entries", response_model=ScientificMemoryEntry, summary="Store Scientific Memory Entry")
async def store_memory_entry(entry: ScientificMemoryEntry) -> ScientificMemoryEntry:
    """
    Stores a validated investigation, empirical benchmark, or negative evidence record.
    Seals cryptographic SHA-256 provenance hash.
    """
    return scientific_memory.add_entry(entry)


@router.get("/entries/{memory_id}", response_model=ScientificMemoryEntry, summary="Get Scientific Memory Entry")
async def get_memory_entry(memory_id: str) -> ScientificMemoryEntry:
    """Retrieves a single scientific memory entry by its identifier."""
    entry = scientific_memory.get_entry(memory_id)
    if not entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Memory entry '{memory_id}' not found.")
    return entry


@router.get("/failures", response_model=List[ScientificMemoryEntry], summary="Retrieve Negative Evidence (Failures)")
async def get_failed_investigations(
    geometry: Optional[str] = Query(default=None, description="Optional geometry filter")
) -> List[ScientificMemoryEntry]:
    """
    Retrieves failure memory records.
    Negative evidence is preserved and searchable to prevent the autonomous loop
    from repeating previously diverged, unphysical, or crashed configurations.
    """
    return scientific_memory.get_failures(geometry=geometry)


@router.get("/stats", response_model=Dict[str, Any], summary="Memory Corpus Statistics")
async def get_memory_stats() -> Dict[str, Any]:
    """Returns overview statistics of scientific memory corpus across types and trust tiers."""
    stats = scientific_memory.get_stats()
    k_stats = epistemic_kernel.get_stats()
    merged = dict(k_stats)
    merged.update(stats)
    merged["total_entries"] = stats.get("total_entries", k_stats.get("total_records", 0))
    merged["total_records"] = k_stats.get("total_records", stats.get("total_entries", 0))
    return merged


@router.get("/trust-tiers", response_model=Dict[str, Dict[str, Any]], summary="List Epistemic Trust Tiers")
async def list_trust_tiers() -> Dict[str, Dict[str, Any]]:
    """
    Returns epistemic trust ranking and numerical priority coefficients.
    Verified empirical and audited CFD results strictly hold higher trust than model-generated text.
    """
    return {
        tier.value: {
            "weight": get_trust_weight(tier),
            "tier_name": tier.name,
            "is_empirical_or_verified": tier in {
                EpistemicTrustTier.VERIFIED_CFD,
                EpistemicTrustTier.REFERENCE_DATA,
                EpistemicTrustTier.EXPERIMENTAL,
            },
        }
        for tier in EpistemicTrustTier
    }


# ────────────────────────────────────────────────────────────────
# 2. Prior-Knowledge Warm Starting (Sweeps & Optimization)
# ────────────────────────────────────────────────────────────────

class WarmStartRequest(BaseModel):
    geometry: str = Field(..., description="E.g. NACA 0012 or NACA 4412")
    alpha_deg: float = Field(default=4.0, description="Target angle of attack in degrees")
    reynolds: float = Field(default=3.0e6, description="Target Reynolds number")
    mach: float = Field(default=0.15, description="Target Mach number")
    target_quantity: str = Field(default="CL", description="Target metric (CL, CD, CM)")


@router.post("/warm-start", response_model=WarmStartProposal, summary="Synthesize Prior-Knowledge Warm Start")
async def get_warm_start_recommendation(req: WarmStartRequest) -> WarmStartProposal:
    """
    Synthesizes prior-knowledge warm-start parameters for parameter sweeps or optimization loops.
    Strictly adheres to Anti-Fabrication Rule: guides solver configuration without fabricating results.
    """
    return epistemic_kernel.get_warm_start(
        geometry=req.geometry,
        alpha_deg=req.alpha_deg,
        reynolds=req.reynolds,
        mach=req.mach,
        target_quantity=req.target_quantity,
    )


# ────────────────────────────────────────────────────────────────
# 3. Cryptographic Merkle-DAG Experiment Lineage
# ────────────────────────────────────────────────────────────────

@router.get("/lineage/{investigation_id}", response_model=List[MerkleLineageNode], summary="Get Investigation Lineage DAG")
async def get_investigation_lineage(investigation_id: str) -> List[MerkleLineageNode]:
    """Retrieves all Merkle lineage blocks for an investigation in causal DAG order."""
    nodes = merkle_lineage.get_investigation_lineage(investigation_id)
    return nodes


@router.get("/lineage/node/{node_id}", response_model=MerkleLineageNode, summary="Get Specific Merkle Lineage Node")
async def get_lineage_node(node_id: str) -> MerkleLineageNode:
    """Retrieves a specific Merkle lineage block by its cryptographic hash."""
    node = merkle_lineage.get_node(node_id)
    if not node:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Merkle node '{node_id}' not found.")
    return node


@router.get("/lineage/node/{node_id}/proof", response_model=Dict[str, Any], summary="Export Cryptographic Audit Proof")
async def get_lineage_proof(node_id: str) -> Dict[str, Any]:
    """Exports independent cryptographic audit receipt and lineage verification trace."""
    node = merkle_lineage.get_node(node_id)
    if not node:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Merkle node '{node_id}' not found.")
    return merkle_lineage.export_audit_proof(node_id)


class VerifyLineageRequest(BaseModel):
    node_id: Optional[str] = None
    investigation_id: Optional[str] = None


@router.post("/lineage/verify", response_model=Dict[str, Any], summary="Verify Cryptographic Lineage Integrity")
async def verify_lineage(req: VerifyLineageRequest) -> Dict[str, Any]:
    """
    Verifies cryptographic integrity of a Merkle node trace or entire investigation DAG.
    """
    if req.node_id:
        return merkle_lineage.verify_lineage_trace(req.node_id)
    elif req.investigation_id:
        root_digest = merkle_lineage.compute_investigation_root(req.investigation_id)
        nodes = merkle_lineage.get_investigation_lineage(req.investigation_id)
        all_valid = all(n.verify_self_hash() for n in nodes)
        return {
            "investigation_id": req.investigation_id,
            "root_digest": root_digest,
            "node_count": len(nodes),
            "integrity_verified": all_valid,
        }
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Must provide node_id or investigation_id.")
