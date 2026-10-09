"""
AASI Aerodynamic Database (Aero DB) API Router.
Handles autonomous flight envelope polar sweeps, stability derivative extraction,
and multi-format aerospace exports (DATCOM, NASA S/HABP, 6-DOF CSV).
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field

from backend.auth.models import User
from backend.auth.dependencies import get_current_user
from backend.physics.aerodb_engine import (
    AerodynamicDatabaseEngine,
    AeroDatabase,
    _AERO_DATABASES,
)
from backend.export.aerodb_export import AeroDBExporter

router = APIRouter(prefix="/aerodb", tags=["Aerodynamic Database & Stability"])


class AeroDBGenerateRequest(BaseModel):
    geometry: str = Field("NACA 0012", description="Geometry identifier or NACA code")
    coordinates_text: Optional[str] = Field(None, description="Optional proprietary coordinate table (.dat/.csv)")
    alpha_min: float = Field(-6.0, description="Minimum angle of attack in degrees")
    alpha_max: float = Field(18.0, description="Maximum angle of attack in degrees")
    alpha_step: float = Field(1.0, description="Angle of attack step in degrees")
    reynolds_list: Optional[List[float]] = Field(default_factory=lambda: [3_000_000.0], description="List of Reynolds numbers")
    mach_list: Optional[List[float]] = Field(default_factory=lambda: [0.15], description="List of Mach numbers")
    fidelity: Optional[str] = Field("MULTI_FIDELITY", description="Fidelity evaluation tier")


@router.post("/generate", response_model=AeroDatabase, summary="Generate Complete Aerodynamic Database & Polars")
async def generate_aerodynamic_database(
    req: AeroDBGenerateRequest,
    user: User = Depends(get_current_user),
):
    """
    Executes autonomous flight envelope sweep across specified alpha, Reynolds,
    and Mach ranges. Calculates stability & control derivatives.
    """
    try:
        aero_db = AerodynamicDatabaseEngine.generate_aero_db(
            geometry_name=req.geometry,
            coordinates_text=req.coordinates_text,
            alpha_min=req.alpha_min,
            alpha_max=req.alpha_max,
            alpha_step=req.alpha_step,
            reynolds_list=req.reynolds_list,
            mach_list=req.mach_list,
            fidelity_tier=req.fidelity or "MULTI_FIDELITY",
        )
        return aero_db
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Aero DB generation failed: {str(exc)}",
        )


@router.get("", summary="List Generated Aerodynamic Databases")
async def list_aerodynamic_databases(user: User = Depends(get_current_user)):
    """
    Lists metadata summaries of all generated aerodynamic databases in memory.
    """
    items = []
    for db_id, db in _AERO_DATABASES.items():
        items.append({
            "db_id": db.db_id,
            "geometry_name": db.geometry_name,
            "created_at_utc": db.created_at_utc,
            "num_conditions": len(db.polars),
            "total_points": db.envelope_summary.get("total_points_evaluated", 0),
            "max_glide_efficiency": db.envelope_summary.get("max_glide_efficiency", 0.0),
            "max_lift_capability": db.envelope_summary.get("max_lift_capability", 0.0),
        })
    return items


@router.get("/{db_id}", response_model=AeroDatabase, summary="Get Full Aerodynamic Database by ID")
async def get_aerodynamic_database(db_id: str, user: User = Depends(get_current_user)):
    """
    Retrieves full aerodynamic database polar records and stability derivatives.
    """
    db = AerodynamicDatabaseEngine.get_aero_db(db_id)
    if not db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Aerodynamic database '{db_id}' not found.",
        )
    return db


@router.get("/{db_id}/export", summary="Export Aerodynamic Database in Aerospace Formats")
async def export_aerodynamic_database(
    db_id: str,
    format: str = Query("datcom", description="Target export format: datcom, shabp, csv, or json"),
    user: User = Depends(get_current_user),
):
    """
    Exports the aerodynamic database into standard aerospace formats:
    - `datcom`: USAF Stability and Control DATCOM standard card deck (.dat)
    - `shabp`: NASA S/HABP tabulated polar format (.shabp)
    - `csv`: 6-DOF simulation lookup tables for Simulink / MATLAB / autopilot (.csv)
    - `json`: Structured JSON schema (.json)
    """
    db = AerodynamicDatabaseEngine.get_aero_db(db_id)
    if not db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Aerodynamic database '{db_id}' not found.",
        )

    clean_geom = db.geometry_name.replace(" ", "_")
    fmt = format.lower().strip()

    if fmt == "datcom":
        content = AeroDBExporter.export_datcom(db)
        return PlainTextResponse(
            content,
            media_type="text/plain",
            headers={"Content-Disposition": f'attachment; filename="{clean_geom}_{db.db_id}.dat"'},
        )
    elif fmt == "shabp":
        content = AeroDBExporter.export_shabp(db)
        return PlainTextResponse(
            content,
            media_type="text/plain",
            headers={"Content-Disposition": f'attachment; filename="{clean_geom}_{db.db_id}.shabp"'},
        )
    elif fmt == "csv":
        content = AeroDBExporter.export_6dof_csv(db)
        return PlainTextResponse(
            content,
            media_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="{clean_geom}_{db.db_id}_6dof.csv"'},
        )
    elif fmt == "json":
        return AeroDBExporter.export_json(db)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported format '{format}'. Supported formats: datcom, shabp, csv, json.",
        )


# ─── Authentic Experimental Wind Tunnel Validation Endpoints (Item 14) ───

@router.get("/experimental/benchmarks", summary="List Authentic Wind Tunnel Benchmark Series")
async def list_experimental_benchmarks():
    """Lists available experimental wind tunnel benchmark series (NASA LTPT, AGARD, UIUC, NACA TR-824)."""
    from backend.science.experimental_validation import experimental_validation_service
    return {"benchmarks": [b.model_dump() for b in experimental_validation_service.list_benchmarks()]}


@router.get("/experimental/{geometry}", summary="Get Ground-Truth Experimental Polar for Geometry")
async def get_experimental_polar(
    geometry: str,
    reynolds: Optional[float] = Query(None, description="Target Reynolds number"),
    mach: Optional[float] = Query(None, description="Target Mach number"),
):
    """Retrieves verified wind tunnel polar points and facility uncertainty bounds for geometry."""
    from backend.science.experimental_validation import experimental_validation_service
    points = experimental_validation_service.get_experimental_polar(geometry, reynolds=reynolds, mach=mach)
    return {
        "geometry": geometry,
        "count": len(points),
        "facility": points[0].facility if points else "Unknown",
        "citation": points[0].citation if points else "None",
        "points": [p.model_dump() for p in points],
    }


class ComparePolarRequest(BaseModel):
    geometry: str
    reynolds: Optional[float] = None
    mach: Optional[float] = None
    predicted_points: List[Dict[str, float]]


@router.post("/experimental/compare", summary="Compare Polar Against Authentic Wind Tunnel Data (ASME V&V 20)")
async def compare_polar_against_wind_tunnel(req: ComparePolarRequest):
    """Executes ASME V&V 20 validation comparing prediction against experimental benchmark."""
    from backend.science.experimental_validation import experimental_validation_service
    result = experimental_validation_service.compare_prediction_against_wind_tunnel(
        geometry=req.geometry,
        predicted_points=req.predicted_points,
        reynolds=req.reynolds,
        mach=req.mach,
    )
    return result.model_dump()


# ─── 3D Surface Pressure & Mesh Visualization (Item 20) ───

from backend.physics.surface_pressure_3d import (
    Surface3DRequest,
    Surface3DResponse,
    generate_3d_surface_pressure,
)


@router.post("/surface-pressure-3d", response_model=Surface3DResponse, summary="Compute 3D Surface Pressure & Mesh Field")
async def get_surface_pressure_3d(req: Surface3DRequest):
    """
    Generates 3D wing geometry, structured CFD surface mesh, and physical
    Cp pressure distribution with transonic shock capturing and chordwise slicing.
    """
    return generate_3d_surface_pressure(req)


# ─── Autonomous Airfoil Shape Optimization (Item 22) ───

from backend.physics.optimization import (
    OptimizationRequest,
    OptimizationResponse,
    run_airfoil_optimization,
)


@router.post("/optimize", response_model=OptimizationResponse, summary="Autonomous Airfoil Shape Optimization")
async def optimize_airfoil_shape(req: OptimizationRequest):
    """
    Performs autonomous shape optimization using Nelder-Mead / sequential quadratic
    descent on thickness and camber parameters to maximize L/D while strictly
    enforcing structural thickness and pitching moment constraints.
    """
    return run_airfoil_optimization(req)



