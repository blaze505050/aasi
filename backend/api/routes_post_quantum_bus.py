"""
Stage 29: Zero-Trust Post-Quantum Spacecraft Bus Security API Endpoints.
Provides REST interface for:
- NIST CRYSTALS-Kyber-1024 (ML-KEM-1024) Key Encapsulation.
- CRYSTALS-Dilithium-5 (ML-DSA-87) Telecommand Digital Signatures.
- CCSDS Anti-Replay Sliding Window and Zero-Trust Telecommand Firewall.
- RAD750 and LEON4 Space Computer Performance Telemetry.
"""

from typing import Any, Dict, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.adapters.neuraloperator_adapter import NeuralOperatorAdapter

router = APIRouter(prefix="/pqc-bus", tags=["Stage 29: Post-Quantum Spacecraft Security"])


class PqcBusAuditRequest(BaseModel):
    spacecraft_id: int = Field(default=0x2A4, description="10-bit Spacecraft ID (CCSDS TC frame)")
    processor_type: str = Field(default="BAE_RAD750_133MHZ", description="BAE_RAD750_133MHZ or COBHAM_LEON4_150MHZ")
    total_frames: int = Field(default=8, ge=1, le=50, description="Total telecommand frames to simulate")
    inject_threats: bool = Field(default=True, description="Whether to inject replay, signature tampering, and spoofed commands")


@router.post("/audit")
def run_bus_audit(request: PqcBusAuditRequest) -> Dict[str, Any]:
    """Runs high-assurance post-quantum zero-trust bus audit against telecommands."""
    try:
        result = NeuralOperatorAdapter.execute_pqc_bus_audit(
            spacecraft_id=request.spacecraft_id,
            processor_type=request.processor_type,
            total_frames=request.total_frames,
            inject_threats=request.inject_threats,
        )
        return {
            "status": "success",
            "data": result,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PQC bus audit failed: {str(e)}")


@router.get("/presets")
def get_bus_presets() -> Dict[str, Any]:
    """Returns available flight processor architectures and mission profiles."""
    try:
        presets = NeuralOperatorAdapter.get_pqc_bus_presets()
        return {
            "status": "success",
            "data": presets,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch presets: {str(e)}")


@router.get("/status")
def get_pqc_spec_status() -> Dict[str, Any]:
    """Returns cryptographic standards and security metrics."""
    return {
        "status": "OPERATIONAL",
        "standards": {
            "key_encapsulation": "CRYSTALS-Kyber-1024 (NIST FIPS 203 / ML-KEM-1024)",
            "digital_signature": "CRYSTALS-Dilithium-5 (NIST FIPS 204 / ML-DSA-87)",
            "hash_function": "SHA3-256 / SHAKE-256 (NIST FIPS 202)",
            "telecommand_protocol": "CCSDS 232.0-B Blue Book / MIL-STD-1553B",
            "security_margin_bits": 256,
            "quantum_attack_immunity": "Shor's and Grover's polynomial-time Shor factorization resistant",
        },
    }
