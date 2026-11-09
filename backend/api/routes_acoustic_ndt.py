"""
Stage 33: Autonomous Ultrasonic & X-Ray CT NDT Defect Inpainting & POD API.
Provides REST endpoints for:
- Ultrasonic pulse-echo A-scan RF synthesis and envelope detection.
- 2D B-scan cross-sectional echogram scanning.
- Micro-CT radiograph attenuation, Otsu flaw segmentation, and physics inpainting.
- MIL-HDBK-1823A Probability of Detection (POD) curve and a_90/95 evaluation.
"""

from typing import Any, Dict, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.adapters.neuraloperator_adapter import NeuralOperatorAdapter
from aasi_aero_fno.acoustic_xray_ndt import NDT_MATERIALS

router = APIRouter(prefix="/acoustic-ndt", tags=["Stage 33: Acoustic & Radiographic NDT Digital Twin"])


class AScanRequest(BaseModel):
    material_key: str = Field(default="TI_6AL_4V", description="TI_6AL_4V, INCONEL_718, or CFRP_LAMINATE")
    specimen_thickness_mm: float = Field(default=25.0, ge=2.0, le=200.0)
    transducer_freq_mhz: float = Field(default=5.0, ge=1.0, le=25.0)
    flaw_depth_mm: Optional[float] = Field(default=12.5, ge=0.5, le=190.0)
    flaw_diameter_um: float = Field(default=350.0, ge=20.0, le=5000.0)
    sampling_rate_mhz: float = Field(default=100.0, ge=20.0, le=500.0)
    snr_db: float = Field(default=28.0, ge=10.0, le=60.0)


class BScanRequest(BaseModel):
    material_key: str = Field(default="TI_6AL_4V")
    specimen_length_mm: float = Field(default=40.0, ge=10.0, le=200.0)
    specimen_thickness_mm: float = Field(default=20.0, ge=5.0, le=100.0)
    flaw_x_mm: float = Field(default=22.0, ge=1.0, le=190.0)
    flaw_depth_mm: float = Field(default=8.5, ge=1.0, le=95.0)
    flaw_diameter_um: float = Field(default=400.0, ge=50.0, le=3000.0)
    scan_steps: int = Field(default=40, ge=10, le=100)


class MicroCtRequest(BaseModel):
    material_key: str = Field(default="TI_6AL_4V")
    grid_size: int = Field(default=64, ge=32, le=128)
    inject_voids: bool = Field(default=True)
    inject_crack: bool = Field(default=True)
    noise_level: float = Field(default=0.04, ge=0.0, le=0.2)


class PodCurveRequest(BaseModel):
    material_key: str = Field(default="TI_6AL_4V")
    inspection_modality: str = Field(default="ULTRASONIC_5MHZ")
    false_call_rate_percent: float = Field(default=1.0, ge=0.1, le=10.0)


@router.post("/ascan")
def run_ascan_simulation(request: AScanRequest) -> Dict[str, Any]:
    """Generates ultrasonic pulse-echo A-scan waveform and envelope."""
    try:
        result = NeuralOperatorAdapter.execute_ndt_ascan(
            material_key=request.material_key,
            specimen_thickness_mm=request.specimen_thickness_mm,
            transducer_freq_mhz=request.transducer_freq_mhz,
            flaw_depth_mm=request.flaw_depth_mm,
            flaw_diameter_um=request.flaw_diameter_um,
            sampling_rate_mhz=request.sampling_rate_mhz,
            snr_db=request.snr_db,
        )
        return {"status": "success", "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"A-scan synthesis failed: {str(e)}")


@router.post("/bscan")
def run_bscan_simulation(request: BScanRequest) -> Dict[str, Any]:
    """Generates 2D ultrasonic B-scan cross-sectional echogram."""
    try:
        result = NeuralOperatorAdapter.execute_ndt_bscan(
            material_key=request.material_key,
            specimen_length_mm=request.specimen_length_mm,
            specimen_thickness_mm=request.specimen_thickness_mm,
            flaw_x_mm=request.flaw_x_mm,
            flaw_depth_mm=request.flaw_depth_mm,
            flaw_diameter_um=request.flaw_diameter_um,
            scan_steps=request.scan_steps,
        )
        return {"status": "success", "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"B-scan synthesis failed: {str(e)}")


@router.post("/micro-ct")
def run_micro_ct_simulation(request: MicroCtRequest) -> Dict[str, Any]:
    """Generates Micro-CT radiograph slice, void segmentation, and physics inpainting."""
    try:
        result = NeuralOperatorAdapter.execute_ndt_ct_slice(
            material_key=request.material_key,
            grid_size=request.grid_size,
            inject_voids=request.inject_voids,
            inject_crack=request.inject_crack,
            noise_level=request.noise_level,
        )
        return {"status": "success", "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Micro-CT simulation failed: {str(e)}")


@router.post("/pod-curve")
def run_pod_curve(request: PodCurveRequest) -> Dict[str, Any]:
    """Generates MIL-HDBK-1823A Probability of Detection curve and a_90/95 thresholds."""
    try:
        result = NeuralOperatorAdapter.compute_pod_evaluation(
            material_key=request.material_key,
            inspection_modality=request.inspection_modality,
            false_call_rate_percent=request.false_call_rate_percent,
        )
        return {"status": "success", "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"POD calculation failed: {str(e)}")


@router.get("/materials")
def get_ndt_materials() -> Dict[str, Any]:
    """Returns acoustic and radiographic material properties."""
    return {
        "status": "success",
        "data": {
            k: {
                "name": v.name,
                "density_kg_per_m3": v.density_kg_per_m3,
                "longitudinal_velocity_mps": round(v.longitudinal_velocity_mps, 1),
                "shear_velocity_mps": round(v.transverse_velocity_mps, 1),
                "acoustic_impedance_mrayls": round(v.acoustic_impedance_mrayls, 2),
                "xray_attenuation_cm_inv": v.xray_attenuation_cm_inv,
            }
            for k, v in NDT_MATERIALS.items()
        },
    }
