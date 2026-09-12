"""
FastAPI application for AASI — Autonomous Aerospace Scientific Intelligence.
Phase 2: Engineering Tool Intelligence.
"""

import logging
from typing import Any, Dict, List, Optional
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from backend.config import settings
from backend.agent import AASIAgent, OllamaUnavailableError, OllamaRuntimeError, default_agent
from backend.tools.registry import tool_registry

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("aasi.backend")

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Backend API for AASI: Experimental AI Research Assistant for Aerospace Engineering & Space Science.",
)

# CORS configuration for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Pydantic Schemas ---

class HealthResponse(BaseModel):
    """Schema for GET /api/health."""
    status: str = Field(..., description="Backend operational status (e.g. 'ok')")
    version: str = Field(..., description="Application version")
    ollama_connected: bool = Field(..., description="Whether Ollama runtime is reachable")
    configured_model: str = Field(..., description="Configured open-weight LLM")
    error: Optional[str] = Field(None, description="Diagnostic error if Ollama is unreachable")


class ChatRequest(BaseModel):
    """Schema for POST /api/chat request body."""
    message: str = Field(..., min_length=1, max_length=16384, description="User query or technical prompt")


class ToolCallInfo(BaseModel):
    """Execution information for a tool invocation."""
    tool: str
    operation: str
    status: str
    trace: List[str] = []


class ChatResponse(BaseModel):
    """Schema for POST /api/chat response."""
    response: str = Field(..., description="AASI AI response or synthesis")
    model: str = Field(..., description="Model identifier that produced the response")
    status: str = Field(default="success", description="Status of the request execution")
    tool_calls: List[ToolCallInfo] = Field(default_factory=list, description="List of tool executions")
    calculations: List[Dict[str, Any]] = Field(default_factory=list, description="Structured numerical outputs")
    verification: Optional[Dict[str, Any]] = Field(None, description="Independent verification results")
    sources: List[Dict[str, Any]] = Field(default_factory=list, description="Cited publications and reports")
    evidence: List[Dict[str, Any]] = Field(default_factory=list, description="Direct cited passage excerpts")
    assumptions: List[str] = Field(default_factory=list, description="Physical and aerodynamic assumptions")
    provenance: List[Dict[str, Any]] = Field(default_factory=list, description="Cryptographic and bibliographical provenance")
    limitations: List[str] = Field(default_factory=list, description="Validity envelope and known limitations")
    dataset_match: Optional[Dict[str, Any]] = Field(None, description="Matched physical dataset if applicable")
    scientific_result: Optional[Dict[str, Any]] = Field(None, description="Detailed scientific result object if resolved")
    resolution_trace: List[str] = Field(default_factory=list, description="Milestones executed in scientific resolution")


class ToolsResponse(BaseModel):
    """Schema for GET /api/tools."""
    tools: List[Dict[str, Any]]


class KnowledgeSearchRequest(BaseModel):
    """Schema for POST /api/knowledge/search."""
    query: str = Field(..., min_length=1, max_length=1000, description="Search query string")
    k: int = Field(default=5, ge=1, le=50, description="Maximum number of passages to return")
    source_filter: Optional[str] = Field(None, description="Filter by source organization (e.g. NASA, NACA)")
    discipline_filter: Optional[str] = Field(None, description="Filter by discipline (e.g. Aerodynamics, Hypersonics)")
    year_min: Optional[int] = Field(None, description="Minimum publication year")
    year_max: Optional[int] = Field(None, description="Maximum publication year")


class DatasetQueryRequest(BaseModel):
    """Schema for POST /api/knowledge/datasets/query."""
    geometry: str = Field(..., description="Airfoil or body geometry (e.g. 'NACA 0012')")
    mach: Optional[float] = Field(None, ge=0.0, description="Mach number")
    reynolds: Optional[float] = Field(None, gt=0.0, description="Reynolds number")
    aoa_deg: Optional[float] = Field(None, description="Angle of attack in degrees")
    domain: str = Field("aerodynamics", description="Physical domain")


class ScienceResolveRequest(BaseModel):
    """Schema for POST /api/science/resolve."""
    query: str = Field(..., min_length=1, max_length=1000, description="Natural language scientific inquiry")


class ScienceNormalizeRequest(BaseModel):
    """Schema for POST /api/science/normalize."""
    query: str = Field(..., min_length=1, max_length=1000, description="Query string to normalize into physical conditions")


class SimulationRunRequest(BaseModel):
    """Schema for POST /api/simulations."""
    case_id: str = Field(..., description="Unique simulation case identifier")
    solver: str = Field("OpenFOAM", description="Target solver: OpenFOAM, SU2, XFOIL, XFLR5")
    geometry: str = Field("NACA 0012", description="Geometry identifier")
    mach: float = Field(0.3, ge=0.0, le=25.0, description="Freestream Mach number")
    reynolds: float = Field(500000.0, gt=0.0, description="Chord-based Reynolds number")
    aoa_deg: float = Field(8.0, ge=-90.0, le=90.0, description="Angle of attack in degrees")
    turbulence_model: str = Field("k-omega SST", description="Turbulence closure model")
    mesh_cells: int = Field(16384, ge=100, description="Nominal cell count")
    run_mode: str = Field("DRY_RUN", description="DRY_RUN, VALIDATION_RUN, FULL_RUN")
    max_iterations: int = Field(1000, ge=1, le=100000, description="Maximum iterations")
    convergence_tolerance: float = Field(1e-6, description="Convergence tolerance")



# --- API Routes ---

@app.get("/api/health", response_model=HealthResponse, summary="System Health Check")
async def get_health():
    """
    Returns backend health, application version, Ollama runtime connectivity,
    and configured model without exposing secrets.
    """
    is_healthy, error_msg = await default_agent.check_health()
    return HealthResponse(
        status="ok",
        version=settings.app_version,
        ollama_connected=is_healthy,
        configured_model=settings.ollama_model,
        error=error_msg,
    )


@app.get("/api/tools", response_model=ToolsResponse, summary="List Registered Tools")
async def get_tools():
    """
    Returns the catalog of available scientific and computational tools.
    """
    return ToolsResponse(tools=tool_registry.list_tools())


# --- Scientific Knowledge & Dataset Endpoints ---

@app.get("/api/knowledge/sources", summary="List Registered Knowledge Sources")
async def list_knowledge_sources():
    """
    Returns registered scientific literature and data repositories with adapter status,
    license handling, and justification notes for unautomated sources.
    """
    from backend.knowledge.service import get_knowledge_service
    svc = get_knowledge_service()
    return {"sources": [m.model_dump() for m in svc.list_sources()]}


@app.post("/api/knowledge/search", summary="Hybrid Literature & Document Search")
async def search_knowledge(request: KnowledgeSearchRequest):
    """
    Performs hybrid retrieval combining FAISS vector similarity, exact technical
    keyword matching, and metadata filtering. Returns passages with full provenance.
    """
    from backend.knowledge.service import get_knowledge_service
    svc = get_knowledge_service()
    results = svc.search_literature(
        query=request.query,
        k=request.k,
        source_filter=request.source_filter,
        discipline_filter=request.discipline_filter,
        year_min=request.year_min,
        year_max=request.year_max,
    )
    return {
        "query": request.query,
        "count": len(results),
        "results": [r.model_dump() for r in results],
    }


@app.get("/api/knowledge/documents", summary="List Ingested Technical Documents")
async def list_documents():
    """Returns catalog of ingested technical reports and papers with provenance hashes."""
    from backend.knowledge.service import get_knowledge_service
    svc = get_knowledge_service()
    return {"documents": svc.list_documents()}


@app.get("/api/knowledge/documents/{document_id}", summary="Get Detailed Document & Provenance")
async def get_document(document_id: str):
    """Returns document metadata, sections, extracted equations, and cryptographic provenance."""
    from backend.knowledge.service import get_knowledge_service
    svc = get_knowledge_service()
    doc = svc.get_document(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail=f"Document '{document_id}' not found in knowledge base.")
    return doc.model_dump()


@app.get("/api/knowledge/datasets", summary="List Registered Physical Datasets")
async def list_datasets(domain: Optional[str] = None, geometry: Optional[str] = None):
    """Returns catalog of registered aerodynamic, CFD, and experimental datasets."""
    from backend.knowledge.service import get_knowledge_service
    svc = get_knowledge_service()
    datasets = svc.list_datasets(domain=domain, geometry=geometry)
    return {"datasets": [d.model_dump() for d in datasets]}


@app.get("/api/knowledge/datasets/{dataset_id}", summary="Get Detailed Dataset by ID")
async def get_dataset(dataset_id: str):
    """Returns complete dataset metadata, flow conditions, and tabular data points."""
    from backend.knowledge.service import get_knowledge_service
    svc = get_knowledge_service()
    ds = svc.get_dataset(dataset_id)
    if not ds:
        raise HTTPException(status_code=404, detail=f"Dataset '{dataset_id}' not found in registry.")
    return ds.model_dump()


@app.post("/api/knowledge/datasets/query", summary="Query Datasets by Flight & Flow Conditions")
async def query_datasets(request: DatasetQueryRequest):
    """
    Searches registered datasets for exact condition matches (geometry, Mach, Reynolds, AoA).
    Returns verified data points with uncertainty bounds.
    """
    from backend.knowledge.service import get_knowledge_service
    svc = get_knowledge_service()
    matches = svc.query_datasets(
        geometry=request.geometry,
        mach=request.mach,
        reynolds=request.reynolds,
        aoa_deg=request.aoa_deg,
        domain=request.domain,
    )
    return {
        "query": request.model_dump(),
        "match_count": len(matches),
        "matches": matches,
    }


# --- Phase 4 Scientific Resolution & Simulation Endpoints ---

@app.post("/api/science/resolve", summary="8-Level Scientific Resolution Hierarchy")
async def resolve_science_query(request: ScienceResolveRequest):
    """
    Orchestrates deterministic scientific result resolution:
    Normalized conditions -> Dataset registry -> Experimental DB -> CFD DB -> Surrogate -> Analytical -> Simulation -> Clarification.
    """
    from backend.science.service import get_science_service
    science_svc = get_science_service()
    return science_svc.engine.resolve(request.query)


@app.post("/api/science/normalize", summary="Normalize Engineering Query into Structured Conditions")
async def normalize_science_query(request: ScienceNormalizeRequest):
    """
    Extracts canonical geometry, Mach, Reynolds, AoA, flow regime, and identifies missing parameters.
    """
    from backend.science.service import get_science_service
    science_svc = get_science_service()
    cond = science_svc.normalizer.normalize(request.query)
    return cond.model_dump()


@app.get("/api/datasets/experimental", summary="List Experimental Database Test Series")
async def list_experimental_datasets(geometry: Optional[str] = None):
    """Returns authentic experimental test measurements with facility and uncertainty bounds."""
    from backend.science.service import get_science_service
    science_svc = get_science_service()
    datasets = science_svc.experimental_db.list_datasets(geometry=geometry)
    return {"experimental_datasets": [d.model_dump() for d in datasets]}


@app.get("/api/datasets/cfd", summary="List Validated CFD Database Records")
async def list_cfd_datasets(geometry: Optional[str] = None):
    """Returns validated and benchmark CFD cases with mesh, turbulence, and residual metadata."""
    from backend.science.service import get_science_service
    science_svc = get_science_service()
    records = science_svc.cfd_db.list_records(geometry=geometry)
    return {"cfd_records": [r.model_dump() for r in records]}


@app.get("/api/surrogates", summary="List Physics Surrogate Models & Envelopes")
async def list_surrogates():
    """Returns registered physics AI surrogates with declared validity envelopes."""
    from backend.science.service import get_science_service
    science_svc = get_science_service()
    surrogates = science_svc.surrogate_registry.list_surrogates()
    return {"surrogates": [s.model_dump() for s in surrogates]}


@app.get("/api/solvers", summary="Discover Host & WSL2 Scientific Solvers")
async def list_solvers():
    """Probes system environment for OpenFOAM, SU2, XFOIL, XFLR5 and returns status."""
    from backend.simulation.registry import solver_registry
    solvers = solver_registry.list_solvers()
    return {"solvers": [s.model_dump() for s in solvers]}


@app.post("/api/simulations", summary="Execute Simulation Run (Dry-Run / Validation / Full)")
async def run_simulation(request: SimulationRunRequest):
    """
    Generates case files and executes simulation run under security sandbox.
    Supports DRY_RUN, VALIDATION_RUN, and FULL_RUN modes.
    """
    from backend.simulation.models import SimulationCase, SimulationRunMode
    from backend.simulation.runner import simulation_runner

    case = SimulationCase(
        case_id=request.case_id,
        solver=request.solver,
        geometry=request.geometry,
        mach=request.mach,
        reynolds=request.reynolds,
        aoa_deg=request.aoa_deg,
        turbulence_model=request.turbulence_model,
        mesh_cells=request.mesh_cells,
        run_mode=SimulationRunMode(request.run_mode),
        max_iterations=request.max_iterations,
        convergence_tolerance=request.convergence_tolerance,
    )

    manifest = simulation_runner.run_case(case)
    return manifest.model_dump()


@app.get("/api/simulations/{case_id}", summary="Get Simulation Manifest and Artifacts")
async def get_simulation_manifest(case_id: str):
    """Retrieves reproducible experiment manifest for simulation case."""
    from pathlib import Path
    import json
    case_path = Path("data/simulations") / case_id / f"EXP-{case_id}.manifest.json"
    if not case_path.exists():
        raise HTTPException(status_code=404, detail=f"Simulation case manifest '{case_id}' not found.")
    return json.loads(case_path.read_text(encoding="utf-8"))



@app.get("/api/science/results/{result_id}", summary="Get Scientific Result and Provenance")
async def get_scientific_result(result_id: str):
    """Inspects detailed scientific result and cryptographic provenance."""
    from backend.science.service import get_science_service
    science_svc = get_science_service()
    for ds in science_svc.experimental_db.list_datasets():
        if result_id in ds.dataset_id:
            return ds.model_dump()
    for rec in science_svc.cfd_db.list_records():
        if result_id in rec.case_id:
            return rec.model_dump()
    raise HTTPException(status_code=404, detail=f"Scientific result '{result_id}' not found.")


# ============================================================================
# PHASE 5 REST ENDPOINTS
# ============================================================================

# Singletons for Phase 5 subsystems
from backend.sources.catalog import ScientificSourceCatalog
from backend.sources.current_info import CurrentInformationService
from backend.datasets.catalog import DatasetCatalog
from backend.datasets.download import DownloadManager
from backend.compute.registry import ComputeBackendRegistry
from backend.compute.models import ComputeRequest, UploadedArtifactPayload
from backend.physics.model_registry import PhysicsModelRegistry
from backend.physics.active_learning import ActiveLearningEngine
from backend.graph.service import KnowledgeGraphService

source_catalog = ScientificSourceCatalog()
current_info_service = CurrentInformationService()
dataset_catalog = DatasetCatalog()
download_manager = DownloadManager()
compute_registry = ComputeBackendRegistry()
physics_model_registry = PhysicsModelRegistry()
knowledge_graph_service = KnowledgeGraphService()


# --- Sources & Federation Endpoints ---

@app.get("/api/sources", summary="List Federated Scientific Sources")
async def list_sources(category: Optional[str] = None, active_only: bool = False):
    """Returns federated sources across 15 scientific disciplines."""
    sources = source_catalog.list_sources(category=category, active_only=active_only)
    return {"sources": [s.model_dump() for s in sources]}


@app.get("/api/sources/diagnostics", summary="Get Runtime Diagnostics for Source Connectors")
async def get_source_diagnostics():
    """Returns runtime operational diagnostics, query counts, and connectivity status."""
    return source_catalog.get_diagnostics()


@app.get("/api/sources/arxiv/search", summary="Search arXiv Fluid Dynamics & Aerodynamics Preprints")
async def search_arxiv(q: str, limit: int = 10):
    """Queries live arXiv preprints with explicit UNVERIFIED_PREPRINT epistemic classification."""
    docs = source_catalog.arxiv_connector.search_documents(q, limit=limit)
    return {
        "query": q,
        "results": [d.model_dump() for d in docs],
        "epistemic_notice": "UNVERIFIED_PREPRINT: Preprints are non-peer-reviewed scholarly manuscripts.",
        "diagnostics": source_catalog.arxiv_connector.get_diagnostics()
    }


@app.get("/api/sources/{source_id}", summary="Get Specific Source Metadata")
async def get_source(source_id: str):
    """Retrieves detailed provenance and access metadata for a scientific source."""
    s = source_catalog.get_source(source_id)
    if not s:
        raise HTTPException(status_code=404, detail=f"Source '{source_id}' not found.")
    return s.model_dump()


@app.get("/api/sources/nasa/search", summary="Search NASA NTRS Records")
async def search_nasa(q: str):
    """Queries authentic public NASA technical reports."""
    results = source_catalog.nasa_adapter.search(q)
    return {"query": q, "results": results}


@app.get("/api/sources/isro/search", summary="Search ISRO Public Registry")
async def search_isro(q: str):
    """Queries verified public ISRO mission and dataset archives."""
    results = source_catalog.isro_adapter.search(q)
    return {"query": q, "results": results}


@app.get("/api/sources/esa/search", summary="Search ESA Public Registry")
async def search_esa(q: str):
    """Queries verified public ESA scientific publications and technical reports."""
    results = source_catalog.esa_adapter.search(q)
    return {"query": q, "results": results}


@app.get("/api/sources/spacex/search", summary="Search Public Commercial Releases")
async def search_spacex(q: str):
    """Queries officially public SpaceX presentations and regulatory documents."""
    is_pub, warning = source_catalog.spacex_adapter.verify_request_is_public(q)
    results = source_catalog.spacex_adapter.search(q)
    return {"query": q, "results": results, "is_public_domain": is_pub, "warning": warning}


# --- Current Events & Spaceflight News Endpoints ---

@app.get("/api/current-info", summary="Get Current Spaceflight Information")
async def get_current_info(limit: int = 10):
    """Returns recent spaceflight events and agency updates labeled STATIC_SEED_DATA."""
    events = current_info_service.get_latest_events(limit=limit)
    return {
        "warning": current_info_service.FRESHNESS_NOTICE,
        "is_live": False,
        "events": [e.model_dump() for e in events]
    }


@app.get("/api/current-info/search", summary="Search Current Spaceflight Events")
async def search_current_info(q: str):
    """Searches current spaceflight events by keywords."""
    events = current_info_service.search_events(q)
    return {
        "warning": current_info_service.FRESHNESS_NOTICE,
        "is_live": False,
        "query": q,
        "events": [e.model_dump() for e in events]
    }


# --- Dataset Factory Endpoints ---

@app.get("/api/datasets/catalog", summary="List Open Physics Dataset Manifests")
async def list_dataset_catalog():
    """Lists high-value open physics datasets with verified manifests."""
    manifests = dataset_catalog.list_manifests()
    return {"datasets": [m.model_dump() for m in manifests]}


@app.get("/api/datasets/manifest/{dataset_id}", summary="Get Dataset Manifest")
async def get_dataset_manifest(dataset_id: str):
    """Returns cryptographic manifest for an open physics dataset."""
    m = dataset_catalog.get_manifest(dataset_id)
    if not m:
        raise HTTPException(status_code=404, detail=f"Dataset manifest '{dataset_id}' not found.")
    return m.model_dump()


@app.post("/api/datasets/download", summary="Trigger Download-on-Demand")
async def download_dataset(dataset_id: str):
    """Executes on-demand download check and verification."""
    m = dataset_catalog.get_manifest(dataset_id)
    if not m:
        raise HTTPException(status_code=404, detail=f"Dataset '{dataset_id}' not found.")
    res = download_manager.download_dataset(m)
    return res
@app.get("/api/datasets/storage-summary", summary="Get Physical Dataset Storage Summary")
async def get_dataset_storage_summary():
    """Reports local vs remote dataset availability, local path, and disk usage."""
    local = dataset_catalog.get_local_datasets()
    remote = dataset_catalog.get_remote_datasets()
    disk = download_manager.check_disk_space(0)
    return {
        "local_datasets_count": len(local),
        "remote_datasets_count": len(remote),
        "local_datasets": [m.model_dump() for m in local],
        "cache_directory": download_manager.cache_dir,
        "disk_info": disk,
    }


@app.get("/api/datasets/tmr-benchmarks", summary="Get NASA TMR 2D Verification Benchmarks")
async def get_tmr_benchmarks():
    """Returns official NASA Turbulence Modeling Resource reference benchmark cases."""
    from backend.datasets.authentic_parsers import NASATMRParser
    return {"benchmarks": [b.model_dump() for b in NASATMRParser.list_benchmarks()]}


class AirfoilParseRequest(BaseModel):
    raw_coordinates: str = Field(..., description="Selig or Lednicer formatted (x, y) coordinate text")
    airfoil_name: Optional[str] = None


@app.post("/api/datasets/airfoil/parse-geometry", summary="Parse and Validate Airfoil Surface Coordinates")
async def parse_airfoil_geometry(req: AirfoilParseRequest):
    """Parses coordinate text, validates chord normalization, and calculates thickness and camber."""
    from backend.datasets.authentic_parsers import UIUCAirfoilParser
    try:
        features = UIUCAirfoilParser.parse_coordinate_text(req.raw_coordinates, req.airfoil_name)
        return features.model_dump()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# --- Compute & User-Executed CFD Endpoints ---

@app.post("/api/compute/generate-case", summary="Generate Standalone aasi_case/ Deck")
async def generate_user_case(req: ComputeRequest):
    """Generates standalone CFD directory with 14-section execution guide."""
    res = compute_registry.dispatch(req)
    return res


@app.post("/api/compute/upload-artifact", summary="Ingest User-Executed Simulation Artifact")
async def upload_artifact(payload: UploadedArtifactPayload):
    """Ingests and validates uploaded simulation logs or polars from external runs."""
    res = compute_registry.artifact_service.ingest_artifact(payload)
    return res.model_dump()


class RouteComputeTaskRequest(BaseModel):
    task_type: str = Field(..., description="e.g. CFD_2D, CFD_3D, SURROGATE_INFERENCE, SURROGATE_TRAINING")
    mesh_cells: int = 0
    dimension: str = "2D"
    solver: str = "openfoam"
    model_type: str = "surrogate"
    sample_count: int = 1000


@app.post("/api/compute/route-request", summary="Evaluate and Route Computational Task Fail-Closed")
async def route_compute_task(req: RouteComputeTaskRequest):
    """Evaluates hardware safety constraints and routes task to LOCAL, USER_EXECUTED, or REMOTE backends."""
    from backend.compute.hardware_matrix import hardware_matrix_manager
    decision = hardware_matrix_manager.route_task(
        task_type=req.task_type,
        mesh_cells=req.mesh_cells,
        dimension=req.dimension,
        solver=req.solver,
        model_type=req.model_type,
        sample_count=req.sample_count,
    )
    return decision.model_dump()


@app.get("/api/system/capabilities", summary="Inspect Host Hardware Capabilities & Safe Computational Regimes")
async def get_system_capabilities():
    """Returns non-fabricated hardware capabilities, memory safety thresholds, and supported solvers."""
    from backend.compute.hardware_matrix import hardware_matrix_manager
    profile = hardware_matrix_manager.detect_hardware()
    return profile.model_dump()



# --- Physics AI Models & Active Learning Endpoints ---

@app.get("/api/physics/models", summary="List Registered Physics AI Models")
async def list_physics_models():
    """Lists registered neural operators and surrogates with verified lifecycle status."""
    models = physics_model_registry.list_models()
    return {"models": [m.model_dump() for m in models]}


@app.get("/api/physics/models/{model_id}/status", summary="Get Physics AI Model Lifecycle & Checkpoint Status")
async def get_model_status(model_id: str):
    """Retrieves lifecycle status, cryptographic checkpoint integrity, and training provenance."""
    model = physics_model_registry.get_model(model_id)
    if not model:
        raise HTTPException(status_code=404, detail=f"Model '{model_id}' not found.")
    verification = physics_model_registry.verify_checkpoint(model_id)
    return {
        "model_id": model_id,
        "lifecycle_status": model.lifecycle_status.value,
        "architecture": model.architecture,
        "verification": verification,
        "training_provenance": model.training_provenance.model_dump() if model.training_provenance else None,
    }


@app.post("/api/physics/models/verify-checkpoints", summary="Verify All Model Checkpoints")
async def verify_all_checkpoints():
    """Performs cryptographic verification across all registered physics models."""
    results = {}
    for m in physics_model_registry.list_models():
        results[m.model_id] = physics_model_registry.verify_checkpoint(m.model_id)
    return {"verifications": results}



class ActiveLearningRequest(BaseModel):
    geometry: str = "NACA 0012"
    reynolds: float = 3.0e6


@app.post("/api/physics/active-learning", summary="Generate Active Learning Simulation Candidates")
async def active_learning_recommendations(req: ActiveLearningRequest):
    """Identifies high-uncertainty regions and recommends targeted CFD simulation cases."""
    # Seed with basic NACA 0012 known points
    known = [
        {"mach": 0.15, "aoa": 0.0},
        {"mach": 0.15, "aoa": 4.0},
        {"mach": 0.30, "aoa": 8.0}
    ]
    candidates = ActiveLearningEngine.identify_sampling_candidates(
        geometry=req.geometry,
        existing_training_points=known,
        reynolds=req.reynolds
    )
    return {"geometry": req.geometry, "candidates": [c.model_dump() for c in candidates]}


# --- Phase 6: Physics-AI Inference, Audit & Grid Convergence Endpoints ---

class AerodynamicPredictRequest(BaseModel):
    geometry: str = Field("naca0012", description="Airfoil designation or name")
    mach: float = Field(0.2, ge=0.01, le=1.0, description="Mach number")
    reynolds: float = Field(2.0e6, ge=1e4, le=5e7, description="Reynolds number")
    aoa_deg: float = Field(4.0, ge=-20.0, le=25.0, description="Angle of attack in degrees")


class AerodynamicPolarRequest(BaseModel):
    geometry: str = Field("naca0012", description="Airfoil designation or name")
    mach: float = Field(0.2, ge=0.01, le=1.0, description="Mach number")
    reynolds: float = Field(2.0e6, ge=1e4, le=5e7, description="Reynolds number")
    aoa_start: float = Field(-4.0, ge=-20.0, le=20.0)
    aoa_end: float = Field(14.0, ge=-20.0, le=25.0)
    aoa_step: float = Field(1.0, ge=0.1, le=5.0)


class GCIRequest(BaseModel):
    f1: float = Field(..., description="Fine grid solution value")
    f2: float = Field(..., description="Medium grid solution value")
    f3: float = Field(..., description="Coarse grid solution value")
    r21: float = Field(1.4142, gt=1.0, description="Grid refinement ratio h2/h1")
    r32: float = Field(1.4142, gt=1.0, description="Grid refinement ratio h3/h2")
    safety_factor: float = Field(1.25, ge=1.0, le=3.0)
    metric_name: str = Field("aerodynamic_coefficient", description="Name of the evaluated metric")


@app.post("/api/physics/aerodynamics/predict", summary="Predict Aerodynamic Coefficients with Epistemic Uncertainty")
async def predict_aerodynamics(req: AerodynamicPredictRequest):
    """Executes AeroSurrogateV1 point inference with epistemic uncertainty and domain classification."""
    from backend.physics_ai.service import PhysicsAIService
    from backend.physics_ai.inference import ModelUnavailableError
    service = PhysicsAIService.get_instance()
    try:
        pred = service.predict(
            geometry=req.geometry,
            mach=req.mach,
            reynolds=req.reynolds,
            aoa_deg=req.aoa_deg
        )
        return pred.model_dump()
    except ModelUnavailableError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e)
        )


@app.post("/api/physics/aerodynamics/polar", summary="Compute Aerodynamic Polar Sweep")
async def polar_sweep_aerodynamics(req: AerodynamicPolarRequest):
    """Computes polar curves (CL vs AoA, CD vs AoA) and verifies monotonicity and drag positivity."""
    from backend.physics_ai.service import PhysicsAIService
    from backend.physics_ai.inference import ModelUnavailableError
    service = PhysicsAIService.get_instance()
    try:
        res = service.polar_sweep(
            geometry=req.geometry,
            mach=req.mach,
            reynolds=req.reynolds,
            aoa_start=req.aoa_start,
            aoa_end=req.aoa_end,
            aoa_step=req.aoa_step
        )
        return res
    except ModelUnavailableError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e)
        )


@app.get("/api/physics/aerodynamics/model-status", summary="Get AeroSurrogate Model Status")
async def get_surrogate_model_status():
    """Returns architecture, weights checksum, parameter count, and operational validity envelope."""
    from backend.physics_ai.service import PhysicsAIService
    service = PhysicsAIService.get_instance()
    return service.get_model_status()


@app.get("/api/physics/audit/datasets", summary="Dataset Authenticity Audit")
async def audit_datasets():
    """Audits all datasets on disk, classifying VERIFIED vs METADATA_ONLY with zero fake science."""
    from backend.datasets.audit import DatasetAuditService
    summary = DatasetAuditService().audit_all()
    return summary.model_dump()



@app.post("/api/validation/grid-convergence", summary="Compute Grid Convergence Index (ASME V&V 20)")
async def compute_grid_convergence(req: GCIRequest):
    """Calculates apparent order p, Richardson extrapolation, and GCI fine/medium."""
    from backend.validation.grid_convergence import GridConvergenceService
    result = GridConvergenceService.compute_gci(
        f1=req.f1,
        f2=req.f2,
        f3=req.f3,
        r21=req.r21,
        r32=req.r32,
        safety_factor=req.safety_factor,
        metric_name=req.metric_name
    )
    return result.model_dump()


@app.get("/api/validation/grid-convergence/benchmarks", summary="Get CFD Mesh Convergence Benchmarks")
async def get_grid_convergence_benchmarks():
    """Returns reference multi-grid CFD mesh convergence benchmarks."""
    from backend.validation.grid_convergence import GridConvergenceService
    return GridConvergenceService.get_benchmark_grid_studies()



# --- Knowledge Graph Endpoints ---

@app.get("/api/graph/entities", summary="Search Scientific Knowledge Graph Entities")
async def search_graph_entities(q: str = ""):
    """Searches knowledge graph entities across 16 scientific entity types."""
    results = knowledge_graph_service.search_entities(q)
    return {"entities": [e.model_dump() for e in results]}


@app.get("/api/graph/neighbors/{entity_id}", summary="Get Knowledge Graph Entity Neighbors")
async def get_graph_neighbors(entity_id: str):
    """Returns connected relations and neighboring entities."""
    neighbors = knowledge_graph_service.get_neighbors(entity_id)
    return {"entity_id": entity_id, "neighbors": neighbors}


# ==========================================
# --- Phase 7 Multi-Fidelity & Research Loop ---
# ==========================================

class MultiFidelityResolveRequest(BaseModel):
    geometry: str = Field("NACA 0012")
    mach: float = Field(0.15, ge=0.01, le=1.5)
    reynolds: float = Field(3.0e6, ge=1e4, le=5e7)
    aoa_deg: float = Field(4.0, ge=-20.0, le=25.0)
    quantity: str = Field("CL")


class ActiveLearningCandidateRequest(BaseModel):
    geometry: str = Field("NACA 0012")
    strategy: str = Field("COST_AWARE")
    max_candidates: int = Field(5, ge=1, le=25)
    cost_weight: float = Field(0.2, ge=0.0, le=1.0)


class CandidateStatusUpdateRequest(BaseModel):
    status: str
    rationale: str = ""
    actor: str = "AASI Researcher"


class CoverageMapRequest(BaseModel):
    geometry: str = Field("NACA 0012")
    plane: str = Field("aoa_vs_mach")


class IngestSimulationRequest(BaseModel):
    file_content: str
    geometry: str
    mach: float
    reynolds: float
    aoa_deg: float
    job_id: Optional[str] = None


class RetrainRequest(BaseModel):
    dataset_version: str = Field("AERO-AIRFOIL-V2.0")
    epochs: int = Field(5, ge=1, le=50)


class SurfaceCpRequest(BaseModel):
    geometry: str = Field("NACA 0012")
    mach: float = Field(0.15, ge=0.01, le=0.85)
    reynolds: float = Field(3.0e6, ge=1e4, le=5e7)
    aoa_deg: float = Field(4.0, ge=-20.0, le=20.0)
    n_chord_points: int = Field(65, ge=20, le=200)


class DimensionalStateRequest(BaseModel):
    mach: Optional[float] = None
    velocity_ms: Optional[float] = None
    temperature_k: float = 288.15
    pressure_pa: float = 101325.0
    chord_m: float = 1.0


class ConstraintCheckRequest(BaseModel):
    cl: float
    cd: float
    cm: float
    mach: float
    aoa_deg: float


@app.post("/api/multifidelity/resolve", summary="Resolve Scientific Query Across 5-Tier Fidelity Hierarchy")
async def resolve_multifidelity(req: MultiFidelityResolveRequest):
    """Deterministically cascades through Tier 1 (Experiment) -> Tier 2 (CFD) -> Tier 5 (Surrogate) -> Tier 4 (Analytical)."""
    from backend.multifidelity.service import multi_fidelity_service
    res = multi_fidelity_service.resolve(
        geometry=req.geometry,
        mach=req.mach,
        reynolds=req.reynolds,
        aoa_deg=req.aoa_deg,
        quantity=req.quantity
    )
    return res


@app.get("/api/multifidelity/calibration", summary="Get Uncertainty Calibration Audit")
async def get_multifidelity_calibration(quantity: str = "CL"):
    """Audits empirical 1-sigma / 2-sigma coverage and epistemic scaling factors against authentic benchmarks."""
    from backend.multifidelity.service import multi_fidelity_service
    metrics = multi_fidelity_service.evaluate_surrogate_calibration(quantity=quantity)
    return metrics.model_dump()


@app.get("/api/multifidelity/statistics", summary="Get Multi-Fidelity Registry Statistics")
async def get_multifidelity_statistics():
    """Returns record count breakdown across EXPERIMENT, CFD, SURROGATE, and ANALYTICAL."""
    from backend.multifidelity.service import multi_fidelity_service
    return multi_fidelity_service.get_statistics()


@app.get("/api/multifidelity/records", summary="Query Multi-Fidelity Registry Records")
async def get_multifidelity_records(geometry: Optional[str] = None, quantity: Optional[str] = None, limit: int = 50):
    from backend.multifidelity.service import multi_fidelity_service
    from backend.multifidelity.models import FidelityLevel
    recs = multi_fidelity_service.registry.query_results(geometry=geometry, quantity=quantity)
    return {"total": len(recs), "records": [r.model_dump() for r in recs[:limit]]}


@app.post("/api/active-learning/candidates", summary="Generate Active Learning Candidates")
async def generate_active_learning_candidates(req: ActiveLearningCandidateRequest):
    """Evaluates parameter space uncertainty and generates ranked candidates using chosen acquisition function."""
    from backend.physics_ai.active_learning import ActiveLearning2Engine, AcquisitionStrategy, active_learning_registry
    from backend.multifidelity.service import multi_fidelity_service
    
    # Query known points
    raw = multi_fidelity_service.query()
    pts = [{"mach": r.conditions.mach, "aoa": r.conditions.aoa_deg, "reynolds": r.conditions.reynolds} for r in raw[:100]]
    
    strat = getattr(AcquisitionStrategy, req.strategy.upper(), AcquisitionStrategy.COST_AWARE)
    candidates = ActiveLearning2Engine.generate_candidates(
        geometry=req.geometry,
        existing_points=pts,
        strategy=strat,
        max_candidates=req.max_candidates,
        cost_weight=req.cost_weight
    )
    # Register them
    for c in candidates:
        active_learning_registry.register_candidate(c)

    return {"candidates": [c.model_dump() for c in candidates]}


@app.get("/api/active-learning/candidates", summary="List Registered Active Learning Candidates")
async def list_active_learning_candidates(geometry: Optional[str] = None, priority: Optional[str] = None):
    from backend.physics_ai.active_learning import active_learning_registry
    cands = active_learning_registry.list_candidates(geometry=geometry, priority=priority)
    return {"candidates": [c.model_dump() for c in cands]}


@app.post("/api/active-learning/candidates/{candidate_id}/status", summary="Update Candidate Lifecycle Status")
async def update_candidate_status(candidate_id: str, req: CandidateStatusUpdateRequest):
    """Updates candidate status: PROPOSED -> APPROVED -> EXECUTED -> INGESTED -> VALIDATED."""
    from backend.physics_ai.active_learning import active_learning_registry, CandidateStatus
    try:
        new_status = CandidateStatus(req.status.upper())
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid candidate status: {req.status}")

    updated = active_learning_registry.update_status(
        candidate_id=candidate_id,
        new_status=new_status,
        rationale=req.rationale,
        actor=req.actor
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Candidate not found")
    return updated.model_dump()


@app.post("/api/active-learning/coverage-map", summary="Get 2D Parameter Coverage Map")
async def get_coverage_map(req: CoverageMapRequest):
    """Generates 2D parameter projection showing sampled, candidate, and unexplored regions."""
    from backend.physics_ai.active_learning import ActiveLearning2Engine, active_learning_registry
    from backend.multifidelity.service import multi_fidelity_service

    raw = multi_fidelity_service.query()
    pts = [{"mach": r.conditions.mach, "aoa": r.conditions.aoa_deg, "reynolds": r.conditions.reynolds} for r in raw[:100]]
    cands = active_learning_registry.list_candidates(geometry=req.geometry)

    cmap = ActiveLearning2Engine.compute_coverage_map(
        geometry=req.geometry,
        existing_points=pts,
        candidate_points=cands,
        plane=req.plane
    )
    return cmap.model_dump()


@app.post("/api/simulation/ingest", summary="Ingest and QC Raw Simulation Artifacts")
async def ingest_simulation_output(req: IngestSimulationRequest):
    """Parses OpenFOAM/CSV log, runs automated QC, and ingests into multi-fidelity registry."""
    from backend.simulation.ingest import SimulationIngestionService
    from backend.multifidelity.models import FlowConditions
    from backend.multifidelity.service import multi_fidelity_service

    cond = FlowConditions(mach=req.mach, reynolds=req.reynolds, aoa_deg=req.aoa_deg)
    results, qc_status, report = SimulationIngestionService.ingest_openfoam_force_coeffs(
        file_content=req.file_content,
        geometry=req.geometry,
        conditions=cond,
        job_id=req.job_id
    )

    # If valid, register in multi-fidelity database
    if report.get("is_valid", False):
        for r in results:
            multi_fidelity_service.registry.register_result(r)

    return {
        "qc_classification": qc_status.value,
        "qc_report": report,
        "ingested_results": [r.model_dump() for r in results]
    }


@app.get("/api/research/objectives", summary="List Scientific Research Objectives")
async def list_research_objectives():
    from backend.research.service import research_loop_service
    return {"objectives": [o.model_dump() for o in research_loop_service.list_objectives()]}


@app.post("/api/research/campaigns/plan", summary="Plan Simulation Campaign for Research Objective")
async def plan_research_campaign(objective_id: str, max_cases: int = 5):
    from backend.research.service import research_loop_service
    camp = research_loop_service.plan_campaign(objective_id=objective_id, max_cases=max_cases)
    if not camp:
        raise HTTPException(status_code=404, detail="Research objective not found")
    return camp.model_dump()


@app.get("/api/research/campaigns", summary="List Simulation Campaigns")
async def list_research_campaigns():
    from backend.research.service import research_loop_service
    return {"campaigns": [c.model_dump() for c in research_loop_service.list_campaigns()]}


@app.post("/api/research/retrain", summary="Trigger Continuous Surrogate Retraining Loop")
async def trigger_retraining_loop(req: RetrainRequest):
    """Executes closed-loop retraining: train candidate -> benchmark test -> compare with V1 -> promotion audit."""
    from backend.research.service import research_loop_service
    summary = research_loop_service.trigger_retraining(
        dataset_version=req.dataset_version,
        epochs=req.epochs
    )
    return summary.model_dump()


@app.get("/api/research/datasets/versions", summary="List Immutable Dataset Versions")
async def list_dataset_versions():
    from backend.datasets.versioning import dataset_version_manager
    return {"versions": [v.model_dump() for v in dataset_version_manager.versions.values()]}


@app.get("/api/research/report/{objective_id}", summary="Generate Scientific Research Report")
async def get_research_report(objective_id: str, format: str = "markdown"):
    from backend.research.service import research_loop_service
    content = research_loop_service.export_report(objective_id=objective_id, format_type=format)
    return {"objective_id": objective_id, "format": format, "content": content}


class ResearchRunCreateRequest(BaseModel):
    question: str
    hypothesis: str = ""
    geometry: str = "NACA 0012"
    flow_conditions: Dict[str, Any] = Field(default_factory=dict)


@app.post("/api/research/runs/execute-flagship", summary="Execute Flagship NACA 0012 Subsonic Research Pipeline")
async def execute_flagship_research_run():
    from backend.research.service import research_loop_service
    run = research_loop_service.execute_flagship_naca0012_run()
    return run.model_dump()


@app.get("/api/research/runs", summary="List All Scientific Research Runs")
async def list_research_runs():
    from backend.research.service import research_loop_service
    return {"runs": [r.model_dump() for r in research_loop_service.list_runs()]}


@app.get("/api/research/runs/{run_id}", summary="Get Details of Specific Research Run")
async def get_research_run(run_id: str):
    from backend.research.service import research_loop_service
    run = research_loop_service.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Research run not found")
    return run.model_dump()


@app.get("/api/research/runs/{run_id}/bundle", summary="Inspect Reproducibility Bundle Manifest")
async def inspect_reproducibility_bundle(run_id: str):
    from backend.research.service import research_loop_service
    from backend.research.bundle import ResearchBundleExporter
    run = research_loop_service.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Research run not found")
    
    bundle_dir, zip_path = ResearchBundleExporter.export_bundle(run)
    hashes_file = bundle_dir / "hashes.sha256"
    hashes_content = hashes_file.read_text(encoding="utf-8") if hashes_file.exists() else ""
    bundle_files = [p.name for p in bundle_dir.iterdir() if p.is_file()]

    return {
        "run_id": run_id,
        "bundle_dir": str(bundle_dir.as_posix()),
        "zip_path": str(zip_path.as_posix()),
        "zip_exists": zip_path.exists(),
        "bundle_files": sorted(bundle_files),
        "hashes": hashes_content,
        "conclusion_level": run.conclusion_level or "MULTI_SOURCE_VALIDATED",
        "merkle_root": run.provenance_trail.get("composite_fingerprint", "")
    }


@app.get("/api/research/runs/{run_id}/export", summary="Download Research Reproducibility Bundle (.zip)")
async def export_reproducibility_bundle_zip(run_id: str):
    from backend.research.service import research_loop_service
    from backend.research.bundle import ResearchBundleExporter
    from fastapi.responses import FileResponse

    run = research_loop_service.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Research run not found")

    _, zip_path = ResearchBundleExporter.export_bundle(run)
    if not zip_path.exists():
        raise HTTPException(status_code=500, detail="Failed to generate reproducibility zip archive")

    clean_id = run.run_id.replace(":", "_").replace("/", "_")
    return FileResponse(
        path=str(zip_path),
        filename=f"aasi_research_run_{clean_id}.zip",
        media_type="application/zip"
    )


@app.post("/api/research/runs", summary="Create and Execute Custom Research Run")
async def create_research_run(req: ResearchRunCreateRequest):
    from backend.research.service import research_loop_service
    run = research_loop_service.create_and_execute_run(
        question=req.question,
        hypothesis=req.hypothesis,
        geometry=req.geometry,
        flow_conditions=req.flow_conditions
    )
    return run.model_dump()


class ReproducibilityVerifyRequest(BaseModel):
    run_id: Optional[str] = None
    bundle_path: Optional[str] = None


@app.post("/api/research/reproduce/verify", summary="Independently Verify Scientific Research Run Reproducibility")
async def verify_research_run_reproducibility(req: ReproducibilityVerifyRequest):
    from backend.research.service import research_loop_service
    from backend.research.verifier import ReproducibilityVerifier
    from pathlib import Path

    if req.bundle_path:
        bundle_dir = Path(req.bundle_path)
        if not bundle_dir.exists():
            raise HTTPException(status_code=404, detail=f"Bundle directory not found: {req.bundle_path}")
        report = ReproducibilityVerifier.verify_bundle_directory(bundle_dir)
        return report.model_dump()
    
    if req.run_id:
        run = research_loop_service.get_run(req.run_id)
        if not run:
            raise HTTPException(status_code=404, detail=f"Research run {req.run_id} not found")
        report = ReproducibilityVerifier.verify_run(run)
        return report.model_dump()
    
    runs = research_loop_service.list_runs()
    flagship_run = next((r for r in runs if r.is_flagship), None)
    if not flagship_run:
        flagship_run = research_loop_service.execute_flagship_naca0012_run()
    report = ReproducibilityVerifier.verify_run(flagship_run)
    return report.model_dump()


@app.get("/api/research/runs/{run_id}/uncertainty", summary="Get 5-Tier Epistemic Uncertainty Assessment")
async def get_run_uncertainty(run_id: str):
    from backend.research.service import research_loop_service
    run = research_loop_service.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Research run not found")
    return run.uncertainty_assessment or {}


@app.get("/api/research/runs/{run_id}/grid-convergence", summary="Get ASME V&V 20 Grid Convergence Study")
async def get_run_grid_convergence(run_id: str):
    from backend.research.service import research_loop_service
    run = research_loop_service.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Research run not found")
    return run.grid_convergence or {}


@app.post("/api/physics/aerodynamics/surface-cp", summary="Predict Chordwise Surface Cp Distribution")
async def predict_surface_cp(req: SurfaceCpRequest):
    from backend.physics_ai.field.surrogate import SurfaceCpSurrogate
    dist = SurfaceCpSurrogate.predict_surface_cp(
        geometry=req.geometry,
        mach=req.mach,
        reynolds=req.reynolds,
        aoa_deg=req.aoa_deg,
        n_chord_points=req.n_chord_points
    )
    return dist.model_dump()


@app.post("/api/physics/dimensional/state", summary="Compute Aerodynamic Dimensional and Dimensionless Flow State")
async def compute_dimensional_flow_state(req: DimensionalStateRequest):
    from backend.physics.dimensional import AerodynamicDimensionalizer
    state = AerodynamicDimensionalizer.compute_flow_state(
        velocity_ms=req.velocity_ms,
        mach=req.mach,
        temperature_k=req.temperature_k,
        pressure_pa=req.pressure_pa,
        chord_m=req.chord_m
    )
    return state.model_dump()


@app.post("/api/physics/constraints/check", summary="Verify Aerodynamic Physical Invariants")
async def check_physical_constraints(req: ConstraintCheckRequest):
    from backend.physics.constraints import AerodynamicConstraintEngine
    report = AerodynamicConstraintEngine.check_aerodynamic_invariants(
        cl=req.cl,
        cd=req.cd,
        cm=req.cm,
        mach=req.mach,
        aoa_deg=req.aoa_deg
    )
    return report.model_dump()


# --- Multi-Dataset Benchmark and Adapter Endpoints ---

class MultiDatasetBenchmarkRequest(BaseModel):
    model_name: str = "AeroSurrogateV1"
    predictions: List[Dict[str, Any]] = Field(default_factory=list)
    dataset_ids: Optional[List[str]] = None


@app.get("/api/datasets/adapters", summary="List Registered Multi-Dataset Adapters")
async def list_dataset_adapters():
    from backend.datasets.catalog import DatasetCatalog
    catalog = DatasetCatalog()
    return catalog.list_adapters()


@app.get("/api/datasets/{dataset_id}/audit", summary="Get Dataset Engineering & Provenance Audit")
async def get_dataset_audit(dataset_id: str):
    from backend.datasets.catalog import DatasetCatalog
    catalog = DatasetCatalog()
    adapter = catalog.get_adapter(dataset_id)
    if not adapter:
        raise HTTPException(status_code=404, detail=f"Dataset adapter '{dataset_id}' not found.")
    manifest = adapter.get_manifest()
    storage_state = adapter.get_storage_state()
    storage_report = adapter.check_storage_safety()
    return {
        "dataset_id": adapter.get_dataset_id(),
        "manifest": manifest.model_dump(),
        "storage_state": storage_state.value,
        "storage_safety_report": storage_report.model_dump(),
        "fields": [f.model_dump() for f in adapter.get_fields()],
        "available_splits": adapter.get_available_splits()
    }


@app.get("/api/datasets/{dataset_id}/cases", summary="List Dataset Cases")
async def list_dataset_cases(dataset_id: str, limit: int = 50, offset: int = 0):
    from backend.datasets.catalog import DatasetCatalog
    catalog = DatasetCatalog()
    adapter = catalog.get_adapter(dataset_id)
    if not adapter:
        raise HTTPException(status_code=404, detail=f"Dataset adapter '{dataset_id}' not found.")
    cases = adapter.list_cases(limit=limit, offset=offset)
    return {
        "dataset_id": dataset_id,
        "total_cases": len(cases),
        "limit": limit,
        "offset": offset,
        "cases": [c.model_dump() for c in cases]
    }


@app.get("/api/datasets/{dataset_id}/splits", summary="Get Dataset IID and OOD Split Partitions")
async def get_dataset_splits(dataset_id: str):
    from backend.datasets.catalog import DatasetCatalog
    catalog = DatasetCatalog()
    adapter = catalog.get_adapter(dataset_id)
    if not adapter:
        raise HTTPException(status_code=404, detail=f"Dataset adapter '{dataset_id}' not found.")
    return {
        "dataset_id": dataset_id,
        "splits": adapter.get_available_splits()
    }


@app.post("/api/datasets/{dataset_id}/validate", summary="Execute Automated Dataset Integrity Validation")
async def validate_dataset(dataset_id: str):
    from backend.datasets.catalog import DatasetCatalog
    from backend.datasets.validation import DatasetValidator
    catalog = DatasetCatalog()
    adapter = catalog.get_adapter(dataset_id)
    if not adapter:
        raise HTTPException(status_code=404, detail=f"Dataset adapter '{dataset_id}' not found.")
    cases = adapter.list_cases(limit=500)
    splits = adapter.get_available_splits()
    report = DatasetValidator.run_full_dataset_validation(
        dataset_id=dataset_id,
        cases=cases,
        splits=splits
    )
    return report.model_dump()


@app.post("/api/datasets/benchmark", summary="Execute Multi-Dataset Aerodynamic Benchmark")
async def run_multi_dataset_benchmark(req: MultiDatasetBenchmarkRequest):
    from backend.physics.multi_benchmark import MultiDatasetBenchmarkEngine
    engine = MultiDatasetBenchmarkEngine()
    result = engine.benchmark_model_predictions(
        model_name=req.model_name,
        predictions=req.predictions,
        dataset_ids=req.dataset_ids
    )
    return result.model_dump()


@app.post("/api/chat", response_model=ChatResponse, summary="AASI Chat and Tool Execution")

async def chat_completion(request: ChatRequest):
    """
    Receives user query, orchestrates AASI agent prompt and context,
    invokes scientific tools or knowledge retrieval, and returns structured synthesis.
    """
    logger.info("Received chat query: '%s...'", request.message[:80])

    try:
        result = await default_agent.process_chat(request.message)
        return ChatResponse(
            response=result["response"],
            model=result["model"],
            status=result["status"],
            tool_calls=result.get("tool_calls", []),
            calculations=result.get("calculations", []),
            verification=result.get("verification"),
            sources=result.get("sources", []),
            evidence=result.get("evidence", []),
            assumptions=result.get("assumptions", []),
            provenance=result.get("provenance", []),
            limitations=result.get("limitations", []),
            dataset_match=result.get("dataset_match"),
            scientific_result=result.get("scientific_result"),
            resolution_trace=result.get("resolution_trace", []),
        )
    except OllamaUnavailableError as exc:
        logger.error("Ollama unavailable: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        )
    except OllamaRuntimeError as exc:
        logger.error("Ollama runtime error: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        )
    except ValueError as exc:
        logger.warning("Invalid request: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        )
    except Exception as exc:
        logger.exception("Unexpected internal error during chat processing: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while processing the request.",
        )


@app.get("/", summary="Root index")
async def root():
    """Root endpoint providing service metadata."""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "docs_url": "/docs",
        "health_url": "/api/health",
        "tools_url": "/api/tools",
        "science_resolve_url": "/api/science/resolve",
        "science_normalize_url": "/api/science/normalize",
        "solvers_url": "/api/solvers",
        "knowledge_sources_url": "/api/knowledge/sources",
        "knowledge_documents_url": "/api/knowledge/documents",
        "knowledge_datasets_url": "/api/knowledge/datasets",
        "experimental_datasets_url": "/api/datasets/experimental",
        "cfd_datasets_url": "/api/datasets/cfd",
        "surrogates_url": "/api/surrogates",
        "system_capabilities_url": "/api/system/capabilities",
    }

