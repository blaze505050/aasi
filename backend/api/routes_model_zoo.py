"""
AASI Physics AI Model Zoo: FastAPI Routes.
Exposes the unified model catalog, verification gate, benchmark engine,
and cross-model comparison for the frontend.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from backend.cognitive.model_zoo import (
    ModelArchitectureFamily,
    ModelMaturityLevel,
    PhysicsDomainCategory,
    ModelInferenceRequest,
    PipelineExecutionRequest,
    model_zoo_registry,
)

router = APIRouter(prefix="/model-zoo", tags=["Physics AI Model Zoo"])


# ─── Request/Response Schemas ────────────────────────────────────────────────────


class ModelZooFilterRequest(BaseModel):
    domain: Optional[str] = None
    architecture: Optional[str] = None
    maturity: Optional[str] = None
    search: Optional[str] = None


class VerifyModelRequest(BaseModel):
    model_id: str
    predictions: Dict[str, Any]
    conservation_residuals: Optional[Dict[str, float]] = None


class CompareModelsRequest(BaseModel):
    model_ids: List[str]
    benchmark_name: Optional[str] = None


# ─── Routes ──────────────────────────────────────────────────────────────────────


@router.get("/catalog")
async def list_model_catalog(
    domain: Optional[str] = Query(None, description="Filter by physics domain"),
    architecture: Optional[str] = Query(None, description="Filter by architecture family"),
    maturity: Optional[str] = Query(None, description="Filter by maturity level"),
    search: Optional[str] = Query(None, description="Free-text search in name/description/tags"),
) -> Dict[str, Any]:
    """Lists all Physics AI models in the catalog with optional filters."""
    domain_enum = None
    arch_enum = None
    mat_enum = None

    if domain:
        try:
            domain_enum = PhysicsDomainCategory(domain)
        except ValueError:
            pass

    if architecture:
        try:
            arch_enum = ModelArchitectureFamily(architecture)
        except ValueError:
            pass

    if maturity:
        try:
            mat_enum = ModelMaturityLevel(maturity)
        except ValueError:
            pass

    models = model_zoo_registry.list_models(
        domain=domain_enum,
        architecture=arch_enum,
        maturity=mat_enum,
        search_query=search,
    )

    return {
        "total": len(models),
        "models": [m.model_dump() for m in models],
        "domains_summary": model_zoo_registry.get_domains_summary(),
        "architectures_summary": model_zoo_registry.get_architectures_summary(),
    }


@router.get("/model/{model_id}")
async def get_model_detail(model_id: str) -> Dict[str, Any]:
    """Returns full descriptor for a specific Physics AI model."""
    model = model_zoo_registry.get_model(model_id)
    if not model:
        raise HTTPException(status_code=404, detail=f"Model '{model_id}' not found in catalog.")
    return model.model_dump()


@router.get("/domains")
async def list_domains() -> Dict[str, Any]:
    """Returns available physics domains and model counts."""
    return {
        "domains": model_zoo_registry.get_domains_summary(),
        "domain_labels": {
            "CFD_FLUID_DYNAMICS": "🌊 CFD / Fluid Dynamics",
            "POROUS_MEDIA_PDE": "💧 Porous Media / PDEs",
            "STRUCTURAL_MECHANICS": "🧱 Structural Mechanics",
            "MATERIALS_MOLECULAR": "⚛️ Materials / Molecular Physics",
            "CONSERVATION_MULTIPHYSICS": "⚡ Conservation Laws / Multiphysics",
        },
    }


@router.get("/architectures")
async def list_architectures() -> Dict[str, Any]:
    """Returns available architecture families and model counts."""
    return {
        "architectures": model_zoo_registry.get_architectures_summary(),
    }


@router.post("/verify")
async def verify_model_output(req: VerifyModelRequest) -> Dict[str, Any]:
    """Runs physics verification gate on model inference output."""
    model = model_zoo_registry.get_model(req.model_id)
    if not model:
        raise HTTPException(status_code=404, detail=f"Model '{req.model_id}' not found.")

    report = model_zoo_registry.verify_model_output(
        model_id=req.model_id,
        predictions=req.predictions,
        conservation_residuals=req.conservation_residuals,
    )
    return report.model_dump()


@router.post("/compare")
async def compare_models(req: CompareModelsRequest) -> Dict[str, Any]:
    """Cross-model comparison on a shared benchmark problem."""
    comparison = model_zoo_registry.compare_models(
        model_ids=req.model_ids,
        benchmark_name=req.benchmark_name,
    )
    return comparison.model_dump()


@router.get("/benchmarks")
async def list_benchmarks(
    domain: Optional[str] = Query(None, description="Filter benchmarks by physics domain"),
) -> List[Dict[str, Any]]:
    """Lists available standardized benchmark problems."""
    domain_enum = None
    if domain:
        try:
            domain_enum = PhysicsDomainCategory(domain)
        except ValueError:
            pass

    problems = model_zoo_registry.benchmark_engine.list_problems(domain=domain_enum)
    return [p.model_dump() for p in problems]


@router.get("/stats")
async def model_zoo_stats() -> Dict[str, Any]:
    """Returns aggregate statistics about the model zoo."""
    all_models = model_zoo_registry.list_models()
    return {
        "total_models": len(all_models),
        "domains": model_zoo_registry.get_domains_summary(),
        "architectures": model_zoo_registry.get_architectures_summary(),
        "maturity_breakdown": {
            level.value: len([m for m in all_models if m.maturity == level])
            for level in ModelMaturityLevel
        },
        "total_benchmarks": len(model_zoo_registry.benchmark_engine.list_problems()),
        "models_with_checkpoints": len([m for m in all_models if m.checkpoint_url]),
        "production_ready_count": len([m for m in all_models if m.maturity == ModelMaturityLevel.PRODUCTION_READY]),
    }


@router.post("/execute")
async def execute_model_inference(req: ModelInferenceRequest) -> Dict[str, Any]:
    """
    Executes a Physics AI Model Zoo model locally.
    Returns aerodynamic/physical force predictions, surface Cp distribution,
    flowfields, conservation residuals, and verification gate status.
    """
    try:
        result = model_zoo_registry.execute_model(req)
        return result.model_dump()
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Execution error: {str(e)}")


@router.post("/pipeline/run")
async def run_connected_pipeline(req: PipelineExecutionRequest) -> Dict[str, Any]:
    """
    Executes the Connected Scientific Pipeline end-to-end:
    Geometry Ingestion -> Physics AI Surrogate -> Verification Gate ->
    Cognitive Brain -> Aero DB Polars -> Flight Dynamics Exporters (DATCOM, SHABP, 6-DOF).
    """
    try:
        result = model_zoo_registry.execute_pipeline(req)
        return result.model_dump()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pipeline execution failed: {str(e)}")


@router.get("/pipeline/presets")
async def get_pipeline_presets() -> List[Dict[str, Any]]:
    """Returns recommended test cases for the Connected Scientific Pipeline."""
    return [
        {
            "name": "NACA 0012 Subsonic Cruise Audit",
            "geometry": "NACA 0012",
            "alpha_deg": 4.0,
            "reynolds": 3.0e6,
            "mach": 0.15,
            "description": "Standard benchmark test for attached potential flow, symmetric drag polar, and pitch stability verification.",
            "recommended_model": "MeshGraphNet",
        },
        {
            "name": "NACA 2412 Cambered Wing Evaluation",
            "geometry": "NACA 2412",
            "alpha_deg": 2.0,
            "reynolds": 2.5e6,
            "mach": 0.20,
            "description": "Cambered airfoil assessing negative zero-lift angle alpha_0L and nose-down pitching moment CM_0.",
            "recommended_model": "Transolver",
        },
        {
            "name": "Clark Y General Aviation Profile",
            "geometry": "Clark Y",
            "alpha_deg": 6.0,
            "reynolds": 1.8e6,
            "mach": 0.12,
            "description": "High-lift general aviation profile testing boundary layer displacement thickness and high L/D peak.",
            "recommended_model": "DPOT",
        },
        {
            "name": "RAE 2822 Transonic Supercritical Shock",
            "geometry": "RAE 2822",
            "alpha_deg": 2.79,
            "reynolds": 6.5e6,
            "mach": 0.725,
            "description": "Supercritical airfoil testing compressibility correction, suction peak flattening, and shock wave positioning.",
            "recommended_model": "DoMINO",
        },
    ]

