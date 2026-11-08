"""
API Routes for Stage 21: Autonomous Cislunar & Lagrange Point Halo Orbit Manifold Navigator (CR3BP).
===================================================================================================
Provides endpoints for Circular Restricted Three-Body Problem dynamics, Earth-Moon L1-L5 libration
points, 3D periodic Halo & NRHO orbit synthesis, Jacobi constant invariant verification, and stable/unstable
invariant manifold tube transfers for zero-propellant lunar gateway insertions.
"""

from typing import Any, Dict, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.adapters.neuraloperator_adapter import NeuralOperatorAdapter

router = APIRouter(prefix="/cislunar", tags=["Stage 21: Cislunar & Halo Orbit Manifold Navigator"])


class CislunarNavigationRequest(BaseModel):
    preset_key: str = Field("ISRO_GAGANYAAN_LUNAR_GATEWAY_L2", description="Target cislunar mission preset")
    override_amplitude_z_km: Optional[float] = Field(None, description="Optional out-of-plane Halo orbit amplitude Az [km]")


@router.post("/navigate")
def navigate_cislunar_manifold(request: CislunarNavigationRequest) -> Dict[str, Any]:
    """
    Computes 3D Halo orbit and stable/unstable invariant manifold transfer tubes in the Earth-Moon synodic frame.
    """
    try:
        return NeuralOperatorAdapter.execute_cislunar_navigation(
            preset_key=request.preset_key,
            override_amplitude_z_km=request.override_amplitude_z_km,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cislunar navigation failed: {str(e)}")


@router.get("/presets")
def get_cislunar_presets() -> Dict[str, Any]:
    """Returns available cislunar mission presets (ISRO Lunar Gateway, Artemis NRHO, WSB Transit)."""
    try:
        return NeuralOperatorAdapter.get_cislunar_presets()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch cislunar presets: {str(e)}")


@router.get("/lagrange-points")
def get_lagrange_points() -> Dict[str, Any]:
    """Returns exact Earth-Moon L1-L5 libration points coordinates, Jacobi constants, and distances."""
    try:
        return NeuralOperatorAdapter.get_lagrange_points()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch Lagrange points: {str(e)}")
