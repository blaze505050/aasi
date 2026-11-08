"""
API Routes for Stage 19: Hardware-in-the-Loop (HIL) 1000 Hz Avionics Testbed.
=============================================================================
Provides endpoints for running 1000 Hz real-time avionics simulation benchmarks,
inspecting microsecond execution latencies, MAVLink v2 / CAN-Aerospace frame counts,
and analyzing in-flight actuator fault recovery metrics.
"""

from typing import Any, Dict, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.adapters.neuraloperator_adapter import NeuralOperatorAdapter

router = APIRouter(prefix="/hil-avionics", tags=["Stage 19: Hardware-in-the-Loop 1000 Hz Avionics Testbed"])


class HILSimulationRequest(BaseModel):
    preset_key: str = Field("PIXHAWK6X_AUTONOMOUS_TRANSITION", description="Avionics testbed preset key")
    override_fault: Optional[str] = Field(None, description="Optional actuator fault override")
    duration_seconds: float = Field(1.0, ge=0.2, le=5.0, description="HIL session duration in seconds")


@router.post("/simulate")
def run_hil_simulation(request: HILSimulationRequest) -> Dict[str, Any]:
    """
    Executes a 1000 Hz real-time HIL avionics hardware-in-the-loop simulation.
    """
    try:
        return NeuralOperatorAdapter.run_hil_avionics_simulation(
            preset_key=request.preset_key,
            override_fault=request.override_fault,
            duration_seconds=request.duration_seconds,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"HIL avionics simulation failed: {str(e)}")


@router.get("/presets")
def get_hil_presets() -> Dict[str, Any]:
    """Returns available HIL avionics testbed presets."""
    try:
        return NeuralOperatorAdapter.get_hil_presets()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch HIL presets: {str(e)}")
