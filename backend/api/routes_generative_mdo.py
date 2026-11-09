"""
Stage 31: Multidisciplinary Topology Optimization to 5-Axis CNC / LPBF Toolpaths API.
Provides REST endpoints for:
- SIMP finite element compliance minimization and volume fraction constraint.
- Overhang angle self-supporting additive manufacturing verification.
- Direct LPBF slicing and laser vector scanpath generation.
"""

from typing import Any, Dict
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.adapters.neuraloperator_adapter import NeuralOperatorAdapter
from aasi_aero_fno.topology_optimization_lpbf import ALLOY_DATABASE

router = APIRouter(prefix="/generative-mdo", tags=["Stage 31: Multidisciplinary Topology Optimization"])


class GenerativeMdoRequest(BaseModel):
    component_name: str = Field(default="TITANIUM_TRANSONIC_WING_RIB", description="Component identifier")
    target_volume_fraction: float = Field(default=0.40, ge=0.20, le=0.80, description="Target volume fraction (e.g. 0.40 for 60% mass reduction)")
    alloy_choice: str = Field(default="TI_6AL_4V", description="TI_6AL_4V, INCONEL_718, or AL_SI10_MG")
    max_iterations: int = Field(default=25, ge=5, le=50, description="Maximum SIMP optimization iterations")


@router.post("/optimize")
def run_mdo_optimization(request: GenerativeMdoRequest) -> Dict[str, Any]:
    """Runs SIMP topology optimization and compiles LPBF additive scanpaths."""
    try:
        result = NeuralOperatorAdapter.execute_generative_mdo(
            component_name=request.component_name,
            target_volume_fraction=request.target_volume_fraction,
            alloy_choice=request.alloy_choice,
            max_iterations=request.max_iterations,
        )
        return {
            "status": "success",
            "data": result,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Generative MDO optimization failed: {str(e)}")


@router.get("/presets")
def get_mdo_presets() -> Dict[str, Any]:
    """Returns available aerospace generative design presets."""
    try:
        presets = NeuralOperatorAdapter.get_generative_mdo_presets()
        return {
            "status": "success",
            "data": presets,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch presets: {str(e)}")


@router.get("/alloys")
def get_alloy_database() -> Dict[str, Any]:
    """Returns certified aerospace alloy physical and LPBF process parameters."""
    return {
        "status": "success",
        "data": {
            alloy.value: {
                "name": props.name,
                "youngs_modulus_gpa": props.youngs_modulus_gpa,
                "density_kg_per_m3": props.density_kg_per_m3,
                "yield_strength_mpa": props.yield_strength_mpa,
                "lpbf_laser_power_w": props.lpbf_laser_power_w,
                "lpbf_scan_speed_mps": props.lpbf_scan_speed_m_per_s,
                "layer_thickness_um": props.layer_thickness_um,
            }
            for alloy, props in ALLOY_DATABASE.items()
        },
    }
