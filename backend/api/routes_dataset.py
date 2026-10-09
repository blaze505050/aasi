"""
AASI Phase 27: Dataset & Object Store API Router.
"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

from backend.auth.models import User
from backend.auth.dependencies import get_current_user
from backend.dataset.object_store import object_store, ArtifactDescriptor, ArtifactCategory, EpistemicClass
from backend.dataset.ingestion import dataset_ingestion_engine, IngestionReport

router = APIRouter(prefix="/dataset", tags=["Dataset & Object Store"])


class IngestDatasetRequest(BaseModel):
    source: str
    license: str
    publication: str
    dataset_version: str
    geometry: str
    flow_conditions: Dict[str, Any]
    solver: str
    mesh: Dict[str, Any]
    results: Dict[str, Any]
    validation_status: str
    notes: Optional[str] = ""


@router.get("/objects", response_model=List[ArtifactDescriptor], summary="List Stored Large Objects")
async def list_objects(category: Optional[ArtifactCategory] = None):
    return object_store.list_artifacts(category=category)


@router.get("/objects/{object_id}", summary="Download or Inspect Large Object")
async def get_object_metadata(object_id: str):
    meta = object_store.head_object(object_id)
    if not meta:
        raise HTTPException(status_code=404, detail="Object not found.")
    return meta.model_dump()


@router.post("/ingest", response_model=IngestionReport, summary="Ingest External CFD Dataset with Provenance")
async def ingest_dataset(
    req: IngestDatasetRequest,
    user: User = Depends(get_current_user),
):
    report = dataset_ingestion_engine.ingest_dataset(req.model_dump())
    if report.status == "REJECTED":
        raise HTTPException(status_code=400, detail=report.message)
    return report


@router.get("/catalog", summary="List Ingested Verified CFD Datasets")
async def list_datasets():
    return dataset_ingestion_engine.list_datasets()


@router.get("/hardware-safety", summary="Host Workstation Hardware & Resource Safety Status")
async def get_hardware_safety_status():
    """
    Evaluates real-time host RAM, disk free reserve, and virtualized dataset safety.
    Guarantees local workstation resources are protected against multi-gigabyte CFD bloat.
    """
    from backend.datasets.safety import WorkstationSafetyGuard
    status = WorkstationSafetyGuard.get_hardware_status()
    return status.model_dump()


@router.get("/universal-benchmarks", summary="Query Global Historical Aerospace CFD & Wind-Tunnel Benchmarks")
async def get_universal_benchmarks(
    family: Optional[str] = None,
    regime: Optional[str] = None,
    geometry_type: Optional[str] = None,
):
    """
    Accesses the master catalog of historical and modern aerospace benchmarks:
    NASA TMR, AGARD Standards, AIAA DPW/HLPW, UIUC Airfoil Database, Abbott & von Doenhoff, and Hypersonic.
    Zero workstation RAM/disk footprint via virtual descriptors.
    """
    from backend.knowledge.universal_cfd_catalog import UniversalCFDOracle
    benchmarks = UniversalCFDOracle.list_benchmarks(family=family, regime=regime, geometry_type=geometry_type)
    return [b.model_dump() for b in benchmarks]


class UniversalPolarRequest(BaseModel):
    geometry: str
    alpha_deg: float
    mach: Optional[float] = 0.15
    reynolds: Optional[float] = 3.0e6


@router.post("/resolve-universal-polar", summary="Instant Zero-Footprint Aerodynamic Benchmark Evaluation")
async def resolve_universal_polar(req: UniversalPolarRequest):
    """
    Resolves calibrated aerodynamic forces (CL, CD, CM, L/D) for ANY aerospace geometry
    in the universal catalog in < 0.5 ms with zero RAM/GPU load.
    """
    from backend.knowledge.universal_cfd_catalog import UniversalCFDOracle
    result = UniversalCFDOracle.resolve_universal_polar(
        geometry=req.geometry,
        alpha_deg=req.alpha_deg,
        mach=req.mach or 0.15,
        reynolds=req.reynolds or 3.0e6,
    )
    return result

