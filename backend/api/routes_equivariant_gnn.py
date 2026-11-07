"""
AASI API: Stage 4 SE(3)-Equivariant 3D Airframe Geometric Graph Neural Network.
Exposes Lie Group continuous equivariance evaluation over SO(3) ⋉ R^3,
3D airframe mesh retrieval (NASA CRM, ADA Tejas, ISRO RLV-TD),
and AIAA / DRDO benchmark validation.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

# Ensure aasi-aero-fno is in path
_pkg_path = Path(__file__).resolve().parent.parent.parent / "aasi-aero-fno"
if str(_pkg_path) not in sys.path:
    sys.path.insert(0, str(_pkg_path))

from backend.adapters.neuraloperator_adapter import (
    NeuralOperatorAdapter,
    AEROSPACE_3D_BENCHMARKS,
)
from aasi_aero_fno.equivariant_gnn import generate_canonical_airframe_mesh

router = APIRouter(prefix="/aero/gnn", tags=["Stage 4 SE(3)-Equivariant 3D Airframe GNN"])


class GNNSolveRequest(BaseModel):
    airframe_type: str = Field(default="nasa_crm", description="Airframe type: 'nasa_crm', 'lca_tejas', 'rlv_td'")
    mach: float = Field(default=0.85, ge=0.05, le=5.0, description="Mach number")
    alpha_deg: float = Field(default=2.2, ge=-10.0, le=45.0, description="Angle of attack in degrees")
    beta_deg: float = Field(default=0.0, ge=-25.0, le=25.0, description="Sideslip angle in degrees")
    reynolds: float = Field(default=5.0e6, ge=1e4, le=1e8, description="Reynolds number")
    yaw_deg: float = Field(default=0.0, ge=-180.0, le=180.0, description="Euler yaw angle in degrees")
    pitch_deg: float = Field(default=0.0, ge=-90.0, le=90.0, description="Euler pitch angle in degrees")
    roll_deg: float = Field(default=0.0, ge=-180.0, le=180.0, description="Euler roll angle in degrees")
    translation_m: List[float] = Field(default=[0.0, 0.0, 0.0], description="3D translation vector [tx, ty, tz] in meters")
    grid_density: int = Field(default=40, ge=20, le=100, description="Grid density parameter")


@router.post("/solve", summary="Solve 3D Airframe Aerodynamics with Exact SE(3) Equivariance")
async def solve_equivariant_gnn(req: GNNSolveRequest) -> Dict[str, Any]:
    """
    Evaluates continuous SE(3)-equivariant geometric graph neural network.
    Guarantees that rotating/translating the airframe in 3D coordinate space
    identically rotates the 3D aerodynamic force and moment vectors with zero scalar drift.
    """
    try:
        translation_tuple: Tuple[float, float, float] = (
            float(req.translation_m[0]) if len(req.translation_m) > 0 else 0.0,
            float(req.translation_m[1]) if len(req.translation_m) > 1 else 0.0,
            float(req.translation_m[2]) if len(req.translation_m) > 2 else 0.0,
        )
        result = NeuralOperatorAdapter.predict_equivariant_3d_airframe(
            airframe_type=req.airframe_type,
            mach=req.mach,
            alpha_deg=req.alpha_deg,
            beta_deg=req.beta_deg,
            reynolds=req.reynolds,
            yaw_deg=req.yaw_deg,
            pitch_deg=req.pitch_deg,
            roll_deg=req.roll_deg,
            translation_m=translation_tuple,
            grid_density=req.grid_density,
        )
        return {
            "status": "SUCCESS",
            "stage": 4,
            "architecture": "SE3_Continuous_Lie_Group_Geometric_Graph_Neural_Network",
            "data": result,
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Equivariant GNN evaluation failed: {str(exc)}")


@router.get("/mesh", summary="Get Canonical 3D Airframe Mesh Points and Reference Geometry")
async def get_airframe_mesh(
    airframe_type: str = Query("nasa_crm", description="Airframe model identifier"),
    grid_density: int = Query(35, ge=15, le=80, description="Surface grid resolution"),
) -> Dict[str, Any]:
    """
    Returns 3D vertices, normals, and reference metrics for interactive WebGL / SVG rendering.
    """
    try:
        mesh = generate_canonical_airframe_mesh(airframe_type, grid_density)
        return {
            "status": "SUCCESS",
            "airframe_name": mesh.name,
            "num_nodes": len(mesh.nodes_xyz),
            "nodes_xyz": [[round(float(v), 4) for v in row] for row in mesh.nodes_xyz],
            "normals_xyz": [[round(float(v), 4) for v in row] for row in mesh.normals_xyz],
            "reference_area_sref": mesh.reference_area_sref,
            "reference_chord_cref": mesh.reference_chord_cref,
            "reference_span_bref": mesh.reference_span_bref,
            "center_of_gravity": [round(float(v), 3) for v in mesh.center_of_gravity],
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to generate airframe mesh: {str(exc)}")


@router.get("/benchmarks", summary="Get 3D Aerospace Reference Datasets (NASA CRM, LCA Tejas, RLV-TD)")
async def get_aerospace_benchmarks() -> Dict[str, Any]:
    """
    Returns verified 3D aerodynamic benchmarks (AIAA DPW-IV, ADA Tejas, ISRO RLV-TD).
    """
    return {
        "status": "SUCCESS",
        "stage": 4,
        "benchmarks": AEROSPACE_3D_BENCHMARKS,
    }

