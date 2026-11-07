"""
AASI API: Stage 10 Automated ASME V&V 20-2009 & NASA-STD-7009B CAS Flight Certification Engine.
Exposes 3-grid Richardson extrapolation, Grid Convergence Index (GCI), asymptotic range checks,
NASA-STD-7009B Credibility Assessment Scale matrix, and cryptographic SHA-256 Merkle flight dossiers.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

# Ensure aasi-aero-fno is in path
_pkg_path = Path(__file__).resolve().parent.parent.parent / "aasi-aero-fno"
if str(_pkg_path) not in sys.path:
    sys.path.insert(0, str(_pkg_path))

from backend.adapters.neuraloperator_adapter import (
    NeuralOperatorAdapter,
    ASME_VV20_BENCHMARKS,
)

router = APIRouter(prefix="/aero/asme-vv20", tags=["Stage 10 ASME V&V 20 Flight Certification"])


class AsmeDossierRequest(BaseModel):
    aircraft_mission: str = Field(default="ISRO RLV-TD Transonic Descent Clearance", description="Flight mission or aircraft identifier")
    target_metric: str = Field(default="Total Lift Coefficient C_L", description="Target aerodynamic or thermal verification metric")
    f1_fine: float = Field(default=0.824, description="Fine grid discrete solution f_1")
    f2_medium: float = Field(default=0.812, description="Medium grid discrete solution f_2")
    f3_coarse: float = Field(default=0.791, description="Coarse grid discrete solution f_3")
    h1_fine: float = Field(default=1.0, gt=0.0, description="Representative fine grid cell dimension h_1")
    h2_medium: float = Field(default=1.414, gt=0.0, description="Representative medium grid cell dimension h_2")
    h3_coarse: float = Field(default=2.0, gt=0.0, description="Representative coarse grid cell dimension h_3")


@router.post("/generate-dossier", summary="Generate Official ASME V&V 20 & NASA-STD-7009B Flight Dossier")
async def generate_flight_dossier(req: AsmeDossierRequest) -> Dict[str, Any]:
    """
    Computes 3-grid Richardson order of accuracy, Roache GCI, asymptotic range check,
    NASA Credibility Assessment Scale (CAS) 8-factor spider score, and signs with SHA-256 Merkle root.
    """
    try:
        result = NeuralOperatorAdapter.generate_flight_certification_dossier(
            aircraft_mission=req.aircraft_mission,
            target_metric=req.target_metric,
            f1_fine=req.f1_fine,
            f2_medium=req.f2_medium,
            f3_coarse=req.f3_coarse,
            h1_fine=req.h1_fine,
            h2_medium=req.h2_medium,
            h3_coarse=req.h3_coarse,
        )
        return {
            "status": "SUCCESS",
            "stage": 10,
            "architecture": "ASME_VV20_Richardson_NASA_STD_7009B_CAS_Engine",
            "data": result,
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"ASME V&V 20 dossier generation failed: {str(exc)}")


@router.get("/benchmarks", summary="Retrieve ASME V&V 20 Canonical Benchmark Datasets")
async def get_asme_vv20_benchmarks() -> Dict[str, Any]:
    """
    Returns canonical AIAA / NASA TMR 3-grid verification benchmark datasets (Flat Plate, CRM, RAE 2822).
    """
    return {
        "status": "SUCCESS",
        "stage": 10,
        "standard": "ASME V&V 20-2009 / NASA-STD-7009B / ASTM F3269-21",
        "benchmarks": NeuralOperatorAdapter.get_asme_vv20_benchmarks(),
    }
