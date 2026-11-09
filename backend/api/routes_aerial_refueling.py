"""
Stage 30: Autonomous Aerial Refueling & Visually-Coupled Docking CBF API Endpoints.
Provides REST interface for:
- Hallock-Burnham heavy tanker wake vortex downwash & sidewash simulation.
- Receiver bow wave aerodynamic repulsion on flexible drogue basket.
- Control Barrier Function Quadratic Program (CBF-QP) safe docking cone enforcement.
- Automated emergency breakaway corridor triggering.
"""

from typing import Any, Dict
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.adapters.neuraloperator_adapter import NeuralOperatorAdapter

router = APIRouter(prefix="/aerial-refueling", tags=["Stage 30: Autonomous Aerial Refueling"])


class AerialRefuelingSimRequest(BaseModel):
    tanker_type: str = Field(default="KC_767", description="KC_767, IL_78, or KC_46")
    receiver_name: str = Field(default="Ghatak UCAV (Autonomous Strike Receiver)", description="Receiver platform name")
    initial_standoff_distance_m: float = Field(default=15.0, ge=3.0, le=50.0, description="Initial standoff distance behind drogue in meters")
    enable_cbf_protection: bool = Field(default=True, description="Enable Control Barrier Function safe cone protection")
    enable_emergency_breakaway_test: bool = Field(default=False, description="Simulate emergency breakaway command during approach")
    turbulence_gust_mps: float = Field(default=3.5, ge=0.0, le=15.0, description="Atmospheric turbulence gust standard deviation in m/s")
    sim_time_sec: float = Field(default=25.0, ge=5.0, le=60.0, description="Simulation duration in seconds")


@router.post("/simulate")
def run_refueling_sim(request: AerialRefuelingSimRequest) -> Dict[str, Any]:
    """Runs autonomous aerial refueling simulation."""
    try:
        result = NeuralOperatorAdapter.execute_aerial_refueling_simulation(
            tanker_type=request.tanker_type,
            receiver_name=request.receiver_name,
            initial_standoff_distance_m=request.initial_standoff_distance_m,
            enable_cbf_protection=request.enable_cbf_protection,
            enable_emergency_breakaway_test=request.enable_emergency_breakaway_test,
            turbulence_gust_mps=request.turbulence_gust_mps,
            sim_time_sec=request.sim_time_sec,
        )
        return {
            "status": "success",
            "data": result,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Aerial refueling simulation failed: {str(e)}")


@router.get("/presets")
def get_refueling_presets() -> Dict[str, Any]:
    """Returns available tanker-receiver mission presets."""
    try:
        presets = NeuralOperatorAdapter.get_aerial_refueling_presets()
        return {
            "status": "success",
            "data": presets,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch presets: {str(e)}")


@router.get("/status")
def get_refueling_specs() -> Dict[str, Any]:
    """Returns aerodynamic and control barrier specifications."""
    return {
        "status": "OPERATIONAL",
        "wake_vortex_model": "Hallock-Burnham with core radius r_c = 0.05 * b",
        "bow_wave_physics": "Airfoil stagnation pressure field bubble repulsion",
        "cbf_formulation": "h_cone(r) = -z - r_xy * cot(theta) >= 0",
        "docking_tolerance_cm": 10.0,
        "nominal_contact_speed_mps": [0.2, 0.8],
    }
