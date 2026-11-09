"""
Stage 35: Digital Thread Merkle Supply Chain & AS9100D Quality Passport API.
Provides REST endpoints for:
- SHA-256 Merkle-DAG component lifecycle traceability and cryptographic tamper audit.
- AS9100D Rev D Statistical Process Control (SPC) Cpk index computation.
- Official FAA Form 8130-3 / DGCA Form 1 Airworthiness Approval Tag synthesizer.
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.adapters.neuraloperator_adapter import NeuralOperatorAdapter

router = APIRouter(prefix="/digital-thread", tags=["Stage 35: Digital Thread & AS9100D Quality Passport"])


class DigitalThreadAuditRequest(BaseModel):
    scenario_preset: str = Field(
        default="TITANIUM_WING_RIB_LPBF",
        description="TITANIUM_WING_RIB_LPBF, INCONEL_TURBINE_BLADE, or CFRP_SPAR_LAMINATE",
    )


class SpcAuditRequest(BaseModel):
    measurements: List[float] = Field(..., description="List of measured dimensions or strength values")
    nominal_target: float = Field(default=190.0)
    lower_spec_limit: float = Field(default=160.0)
    upper_spec_limit: float = Field(default=220.0)
    spec_unit: str = Field(default="μm")


class Certificate8130Request(BaseModel):
    part_name: str = Field(default="TITANIUM_TRANSONIC_WING_RIB")
    part_number: str = Field(default="AASI-LPBF-TI64-001")
    serial_number: str = Field(default="SN-2026-X892")
    material_spec: str = Field(default="AMS 4928 Ti-6Al-4V")
    merkle_root_hash: str = Field(default="a1b2c3d4e5f60718293a4b5c6d7e8f90a1b2c3d4e5f60718293a4b5c6d7e8f90")
    cpk_score: float = Field(default=1.72)
    authority: str = Field(default="FAA / DGCA")


@router.post("/audit")
def run_digital_thread_audit(request: DigitalThreadAuditRequest) -> Dict[str, Any]:
    """Generates complete SHA-256 Merkle-DAG lifecycle digital thread and AS9100D audit."""
    try:
        result = NeuralOperatorAdapter.execute_digital_thread_audit(
            scenario_preset=request.scenario_preset
        )
        return {"status": "success", "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Digital thread audit failed: {str(e)}")


@router.post("/spc-cpk")
def run_spc_audit(request: SpcAuditRequest) -> Dict[str, Any]:
    """Computes AS9100D Process Capability Indices (Cp, Cpk) from measured samples."""
    try:
        result = NeuralOperatorAdapter.execute_as9100d_spc_audit(
            measurements=request.measurements,
            nominal_target=request.nominal_target,
            lower_spec_limit=request.lower_spec_limit,
            upper_spec_limit=request.upper_spec_limit,
            spec_unit=request.spec_unit,
        )
        return {"status": "success", "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"SPC audit failed: {str(e)}")


@router.post("/certificate-8130")
def create_airworthiness_tag(request: Certificate8130Request) -> Dict[str, Any]:
    """Generates official FAA Form 8130-3 / DGCA Form 1 Airworthiness Approval Tag."""
    try:
        result = NeuralOperatorAdapter.execute_generate_faa_8130(
            part_name=request.part_name,
            part_number=request.part_number,
            serial_number=request.serial_number,
            material_spec=request.material_spec,
            merkle_root_hash=request.merkle_root_hash,
            cpk_score=request.cpk_score,
            authority=request.authority,
        )
        return {"status": "success", "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Certificate generation failed: {str(e)}")


@router.get("/presets")
def get_digital_thread_presets() -> Dict[str, Any]:
    """Returns available aerospace component presets for digital thread generation."""
    return {
        "status": "success",
        "data": {
            "presets": [
                {
                    "key": "TITANIUM_WING_RIB_LPBF",
                    "title": "Ti-6Al-4V Transonic Wing Rib (Additive LPBF)",
                    "material": "AMS 4928 Ti-6Al-4V Grade 5",
                    "manufacturing": "EOS M400-4 5-Axis Additive + Hermle C42 CNC",
                },
                {
                    "key": "INCONEL_TURBINE_BLADE",
                    "title": "Inconel 718 High-Pressure Turbine Blade",
                    "material": "AMS 5662 Nickel Alloy Superalloy",
                    "manufacturing": "LPBF Micro-Lattice + Vacuum HIP Aging",
                },
                {
                    "key": "CFRP_SPAR_LAMINATE",
                    "title": "IM7/8552 Carbon Fiber Primary Wing Spar",
                    "material": "Hexcel IM7/8552 Quasi-Isotropic [0/45/-45/90]2s",
                    "manufacturing": "Automated Fiber Placement (AFP) + Autoclave 180°C",
                },
            ]
        },
    }
