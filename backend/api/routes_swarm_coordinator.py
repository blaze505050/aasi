"""
API Routes for Stage 26: Autonomous Heterogeneous UAV Swarm Tactical Coordinator.
==================================================================================
Endpoints for:
- Simulating multi-UAV swarm tactical operations under Control Barrier Functions (CBF).
- Executing Byzantine Fault Tolerant (BFT) distributed consensus checks under EW jamming.
- Evaluating aerodynamic wake upwash and induced drag reductions in formation flight.
"""

from typing import Any, Dict
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.adapters.neuraloperator_adapter import NeuralOperatorAdapter

router = APIRouter(prefix="/swarm", tags=["Stage 26: Heterogeneous UAV Swarm Tactical Coordinator"])


class SwarmSimulateRequest(BaseModel):
    mission_id: str = Field("INDIAN_AF_ALFAS_SWARM", description="Swarm mission ID")
    formation_type: str = Field("V_FORMATION", description="Target formation (V_FORMATION, DEFENSIVE_RING, PINCER_ENVELOPMENT, DISTRIBUTED_MESH)")
    num_uavs: int = Field(18, description="Number of heterogeneous UAV agents (8 to 48)")
    d_safe: float = Field(12.0, description="Control Barrier Function minimum safety distance (meters)")
    byzantine_adversary_present: bool = Field(False, description="Whether to inject rogue/jammed adversarial nodes")
    steps: int = Field(60, description="Simulation steps")


@router.post("/simulate")
def simulate_swarm(request: SwarmSimulateRequest) -> Dict[str, Any]:
    """
    Executes a high-fidelity swarm coordination simulation with CBF collision guarantees and BFT consensus.
    """
    try:
        return NeuralOperatorAdapter.execute_swarm_simulation(
            mission_id=request.mission_id,
            formation_type=request.formation_type,
            num_uavs=request.num_uavs,
            d_safe=request.d_safe,
            byzantine_adversary_present=request.byzantine_adversary_present,
            steps=request.steps,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Swarm simulation failed: {str(e)}")


@router.get("/presets")
def get_swarm_presets() -> Dict[str, Any]:
    """Returns available tactical swarm mission presets."""
    try:
        return NeuralOperatorAdapter.get_swarm_presets()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch swarm presets: {str(e)}")


@router.get("/status")
def get_swarm_status() -> Dict[str, Any]:
    """Returns the operational status of the Swarm Tactical Coordinator."""
    return {
        "status": "OPERATIONAL",
        "cbf_safety_guarantee": "PROVABLE_QUADRATIC_PROGRAMMING",
        "byzantine_tolerance_limit": "f < n / 3",
        "aerodynamic_wake_model": "Prandtl-Horseshoe Upwash",
        "max_swarm_capacity": 64,
    }
