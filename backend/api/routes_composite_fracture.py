"""
Stage 34: Composite Layup & Fracture Mechanics Cohesive Zone API.
Provides REST endpoints for:
- Classical Laminate Theory (CLT) ABD stiffness matrix and engineering constants.
- 3D Tsai-Wu interactive quadratic failure envelope and safety margins.
- Bilinear Cohesive Zone Modeling (CZM) delamination with Benzeggagh-Kenane (B-K) mixed-mode criterion.
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.adapters.neuraloperator_adapter import NeuralOperatorAdapter
from aasi_aero_fno.composite_fracture_czm import COMPOSITE_DB, STANDARD_LAYUPS

router = APIRouter(prefix="/composite-fracture", tags=["Stage 34: Composite Layup & Fracture Mechanics"])


class CltRequest(BaseModel):
    material_key: str = Field(default="IM7_8552", description="IM7_8552 or E_GLASS_913")
    ply_angles_deg: Optional[List[float]] = Field(default=None, description="List of ply angles in degrees")


class TsaiWuRequest(BaseModel):
    material_key: str = Field(default="IM7_8552")
    sigma1_mpa: float = Field(default=800.0, description="Longitudinal stress in MPa")
    sigma2_mpa: float = Field(default=35.0, description="Transverse stress in MPa")
    tau12_mpa: float = Field(default=40.0, description="In-plane shear stress in MPa")


class CzmRequest(BaseModel):
    material_key: str = Field(default="IM7_8552")
    applied_normal_opening_um: float = Field(default=12.0, ge=0.0, le=100.0)
    applied_shear_sliding_um: float = Field(default=8.0, ge=0.0, le=100.0)
    interface_penalty_stiffness_kpa_um: float = Field(default=1.0e5, ge=1e3, le=1e7)


@router.post("/clt-abd")
def compute_clt_laminate(request: CltRequest) -> Dict[str, Any]:
    """Calculates Classical Laminate Theory ABD stiffness matrices."""
    try:
        result = NeuralOperatorAdapter.execute_clt_composite_analysis(
            material_key=request.material_key,
            ply_angles_deg=request.ply_angles_deg,
        )
        return {"status": "success", "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"CLT calculation failed: {str(e)}")


@router.post("/tsai-wu")
def evaluate_tsai_wu(request: TsaiWuRequest) -> Dict[str, Any]:
    """Evaluates 3D Tsai-Wu failure criterion and generates 2D envelope."""
    try:
        result = NeuralOperatorAdapter.execute_tsai_wu_evaluation(
            material_key=request.material_key,
            sigma1_mpa=request.sigma1_mpa,
            sigma2_mpa=request.sigma2_mpa,
            tau12_mpa=request.tau12_mpa,
        )
        return {"status": "success", "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Tsai-Wu evaluation failed: {str(e)}")


@router.post("/czm-delamination")
def simulate_czm(request: CzmRequest) -> Dict[str, Any]:
    """Simulates mixed-mode Bilinear CZM delamination and B-K fracture curve."""
    try:
        result = NeuralOperatorAdapter.execute_czm_delamination_simulation(
            material_key=request.material_key,
            applied_normal_opening_um=request.applied_normal_opening_um,
            applied_shear_sliding_um=request.applied_shear_sliding_um,
            interface_penalty_stiffness_kpa_um=request.interface_penalty_stiffness_kpa_um,
        )
        return {"status": "success", "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"CZM simulation failed: {str(e)}")


@router.get("/presets")
def get_composite_presets() -> Dict[str, Any]:
    """Returns database of composite materials and standard aerospace layups."""
    return {
        "status": "success",
        "data": {
            "materials": {
                k: {
                    "name": v.name,
                    "e1_gpa": v.e1_gpa,
                    "e2_gpa": v.e2_gpa,
                    "g12_gpa": v.g12_gpa,
                    "nu12": v.nu12,
                    "ply_thickness_mm": v.ply_thickness_mm,
                    "xt_mpa": v.xt_mpa,
                    "xc_mpa": v.xc_mpa,
                    "yt_mpa": v.yt_mpa,
                    "yc_mpa": v.yc_mpa,
                    "s12_mpa": v.s12_mpa,
                    "g_ic_kj_m2": v.g_ic_kj_m2,
                    "g_iic_kj_m2": v.g_iic_kj_m2,
                }
                for k, v in COMPOSITE_DB.items()
            },
            "standard_layups": STANDARD_LAYUPS,
        },
    }
