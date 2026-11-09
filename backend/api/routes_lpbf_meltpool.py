"""
Stage 32: In-Situ LPBF Melt-Pool PINN Digital Twin API Endpoints.
Provides REST interface for:
- Rosenthal 3D thermal conduction & melt-pool dimension extraction.
- Marangoni thermocapillary surface flow and convection stress.
- Defect regime diagnosis (Keyholing, Lack of Fusion, Balling).
- 100 kHz Coaxial Pyrometer telemetry and feedforward power control simulation.
"""

from typing import Any, Dict
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.adapters.neuraloperator_adapter import NeuralOperatorAdapter
from aasi_aero_fno.lpbf_meltpool_pinn import ALLOY_THERMAL_DB

router = APIRouter(prefix="/lpbf-meltpool", tags=["Stage 32: LPBF Melt-Pool PINN Digital Twin"])


class MeltPoolSolveRequest(BaseModel):
    laser_power_w: float = Field(default=280.0, ge=50.0, le=1000.0, description="Laser power in Watts")
    scan_speed_mps: float = Field(default=1.2, ge=0.1, le=5.0, description="Laser scan velocity in m/s")
    beam_radius_um: float = Field(default=50.0, ge=20.0, le=200.0, description="Laser beam waist radius in microns")
    layer_thickness_um: float = Field(default=40.0, ge=20.0, le=100.0, description="Powder layer thickness in microns")
    alloy_key: str = Field(default="TI_6AL_4V", description="TI_6AL_4V or INCONEL_718")


class PyrometerScanRequest(BaseModel):
    alloy_key: str = Field(default="TI_6AL_4V", description="TI_6AL_4V or INCONEL_718")
    nominal_laser_power_w: float = Field(default=280.0, ge=50.0, le=800.0)
    scan_speed_mps: float = Field(default=1.2, ge=0.1, le=3.0)
    enable_feedforward_control: bool = Field(default=True, description="Enable active power modulation")
    inject_overhang_geometry: bool = Field(default=True, description="Simulate thin-wall / overhang feature")
    scan_track_length_mm: float = Field(default=20.0, ge=5.0, le=50.0)


@router.post("/solve")
def solve_meltpool(request: MeltPoolSolveRequest) -> Dict[str, Any]:
    """Computes 3D Rosenthal melt-pool dimensions and defect regime."""
    try:
        result = NeuralOperatorAdapter.execute_meltpool_simulation(
            laser_power_w=request.laser_power_w,
            scan_speed_mps=request.scan_speed_mps,
            beam_radius_um=request.beam_radius_um,
            layer_thickness_um=request.layer_thickness_um,
            alloy_key=request.alloy_key,
        )
        return {
            "status": "success",
            "data": result,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Melt-pool calculation failed: {str(e)}")


@router.post("/pyrometer-scan")
def run_pyrometer_scan(request: PyrometerScanRequest) -> Dict[str, Any]:
    """Simulates coaxial pyrometer telemetry and closed-loop laser power adaptation."""
    try:
        result = NeuralOperatorAdapter.execute_pyrometer_scanpass(
            alloy_key=request.alloy_key,
            nominal_laser_power_w=request.nominal_laser_power_w,
            scan_speed_mps=request.scan_speed_mps,
            enable_feedforward_control=request.enable_feedforward_control,
            inject_overhang_geometry=request.inject_overhang_geometry,
            scan_track_length_mm=request.scan_track_length_mm,
        )
        return {
            "status": "success",
            "data": result,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pyrometer scan simulation failed: {str(e)}")


@router.get("/alloys")
def get_alloy_thermal_db() -> Dict[str, Any]:
    """Returns thermal properties of alloys for LPBF simulation."""
    return {
        "status": "success",
        "data": {
            k: {
                "name": v.name,
                "melting_temperature_c": round(v.melting_temperature_k - 273.15, 1),
                "boiling_temperature_c": round(v.boiling_temperature_k - 273.15, 1),
                "laser_absorptivity": v.laser_absorptivity,
                "thermal_conductivity": v.thermal_conductivity_w_per_m_k,
                "density": v.density_kg_per_m3,
            }
            for k, v in ALLOY_THERMAL_DB.items()
        },
    }
