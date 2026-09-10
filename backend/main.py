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
    """Returns recent spaceflight events and agency updates labeled CURRENT_INFORMATION."""
    events = current_info_service.get_latest_events(limit=limit)
    return {"events": [e.model_dump() for e in events]}


@app.get("/api/current-info/search", summary="Search Current Spaceflight Events")
async def search_current_info(q: str):
    """Searches current spaceflight events by keywords."""
    events = current_info_service.search_events(q)
    return {"query": q, "events": [e.model_dump() for e in events]}


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


# --- Physics AI Models & Active Learning Endpoints ---

@app.get("/api/physics/models", summary="List Registered Physics AI Models")
async def list_physics_models():
    """Lists registered neural operators and surrogates (AeroGraphNet, FNO, etc.)."""
    models = physics_model_registry.list_models()
    return {"models": [m.model_dump() for m in models]}


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
    }

