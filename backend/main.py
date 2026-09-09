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
        "knowledge_sources_url": "/api/knowledge/sources",
        "knowledge_documents_url": "/api/knowledge/documents",
        "knowledge_datasets_url": "/api/knowledge/datasets",
    }
