"""
AASI-Craft API Router.
Exposes endpoints for the 4-step reverse-engineering and verification loop:
- /api/v2/craft/study
- /api/v2/craft/build
- /api/v2/craft/check
- /api/v2/craft/ready
- /api/v2/craft/pipeline
- /api/v2/craft/presets
"""

from __future__ import annotations
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

root_dir = Path(__file__).resolve().parent.parent.parent
for mod_name in ["aasi-craft", "aasi-orbital-gnc", "aasi-aero-fno", "aasi-constitution-rta"]:
    mod_path = root_dir / mod_name
    if str(mod_path) not in sys.path:
        sys.path.insert(0, str(mod_path))

from aasi_craft.evidence_dossier import EvidenceDossier
from aasi_craft.parsers.polar_parser import AirfoilPolarParser
from aasi_craft.parsers.telemetry_parser import CcsdsTelemetryParser
from aasi_craft.synthesis.clean_room_synthesizer import CleanRoomSynthesizer
from aasi_craft.verification.asme_vv20 import AsmeVv20Verifier
from aasi_craft.assurance.rta_packager import RtaAirworthinessPackager
from aasi_craft.cad.geometry_engine import CadGeometryEngine
from aasi_craft.mesher.automated_mesher import AutomatedMesher
from aasi_craft.exporters.autopilot_exporter import AutopilotHardwareExporter
from aasi_orbital_gnc.hil_bridge import HilFlightBridge, HilFailureMode
from aasi_aero_fno.adaskip_tmr import TmrRadiationExecutive
from aasi_craft.flagship_workflow import (
    run_naca4412_surrogate_pipeline,
    run_spadex_eclipse_docking_pipeline,
    NACA_4412_EXPERIMENTAL_POLAR,
)

# Global HIL singleton bridge
hil_bridge_singleton = HilFlightBridge()
tmr_exec_singleton = TmrRadiationExecutive()

router = APIRouter(prefix="/api/v2/craft", tags=["AASI-Craft Reverse Engineering"])


class StudyRequest(BaseModel):
    preset: str = Field(default="naca4412", description="Built-in preset: naca4412, spadex")
    file_content: Optional[str] = None
    target_name: Optional[str] = None


class CheckRequest(BaseModel):
    f1_fine: float = Field(default=1.670, description="Fine grid metric value")
    f2_medium: float = Field(default=1.658, description="Medium grid metric value")
    f3_coarse: float = Field(default=1.625, description="Coarse grid metric value")
    refinement_ratio: float = Field(default=2.0, ge=1.1, description="Grid refinement ratio")
    metric_name: str = Field(default="CL_max", description="Target metric name")


class ReadyRequest(BaseModel):
    target_name: str = "NACA_4412"
    merkle_root: str
    is_asme_vv20_verified: bool = True
    action_type: str = "DEPLOY_TO_FLIGHT_COMPUTER"
    summary: str = "Authorize deployment of verified surrogate model"
    auto_approve: bool = True


class PipelineRequest(BaseModel):
    preset: str = Field(default="naca4412", description="naca4412 or spadex")
    auto_approve: bool = Field(default=True, description="Auto-approve RTA flight safety cards")


@router.get("/presets")
def get_flagship_presets() -> Dict[str, Any]:
    """Returns available flagship aerospace reverse-engineering presets."""
    return {
        "presets": [
            {
                "id": "naca4412",
                "title": "NACA 4412 Transonic Aerodynamic Surrogate",
                "domain": "Aerodynamics & CFD",
                "description": "Clean-room FourNetFlows surrogate synthesis from NASA LTPT wind tunnel polar. ASME V&V 20 3-grid Richardson verification.",
                "target_type": "WIND_TUNNEL_POLAR",
                "status": "READY_FOR_STUDY",
            },
            {
                "id": "spadex",
                "title": "ISRO SpaDeX-2 / BAS-01 Rendezvous Sensor Fusion",
                "domain": "Orbital GNC & Space Missions",
                "description": "CCSDS Blue Book telemetry ingestion and NavIC+ISL filter synthesis. Eliminates 225m post-eclipse drift anomaly.",
                "target_type": "TELEMETRY_STREAM",
                "status": "READY_FOR_STUDY",
            },
            {
                "id": "catfm_monsoon",
                "title": "AAI C-ATFM Monsoon Network Flow Optimizer",
                "domain": "National Airspace Systems",
                "description": "Ingests Mumbai FIR radar convective squalls and calculates fuel-optimal Ground Delay Programs.",
                "target_type": "AIRSPACE_SCHEDULE",
                "status": "READY_FOR_STUDY",
            },
            {
                "id": "netra_debris",
                "title": "Project NETRA Orbital Conjunction & CAM Burn",
                "domain": "Space Situational Awareness",
                "description": "Multi-radar track ingestion, Foster 2D collision probability calculation, and optimal delta-v maneuver planning.",
                "target_type": "RADAR_TRACK",
                "status": "READY_FOR_STUDY",
            },
        ]
    }


@router.post("/study")
def post_study(req: StudyRequest) -> Dict[str, Any]:
    """Executes deterministic study phase on target polar or stream."""
    if req.preset.lower() == "naca4412":
        content = req.file_content or NACA_4412_EXPERIMENTAL_POLAR
        dossier = AirfoilPolarParser.parse_csv_stream(content, airfoil_name=req.target_name or "NACA_4412")
        return dossier.to_dict()
    elif req.preset.lower() == "spadex":
        # Create representative packet stream
        stream = bytearray()
        for i in range(10):
            pkt = CcsdsTelemetryParser.create_ccsds_packet(
                apid=0x042A,
                seq_count=i,
                timestamp_s=float(i * 10),
                pos_xyz=(100.0 - i * 9.0, 0.0, 0.0),
                vel_xyz=(-0.12, 0.0, 0.0),
                quat_wxyz=(1.0, 0.0, 0.0, 0.0),
            )
            stream.extend(pkt)
        dossier = CcsdsTelemetryParser.parse_telemetry_stream(bytes(stream), stream_name="SPADEX_2_TLM")
        return dossier.to_dict()
    raise HTTPException(status_code=400, detail=f"Unsupported preset: {req.preset}")


@router.post("/check")
def post_check(req: CheckRequest) -> Dict[str, Any]:
    """Executes ASME V&V 20 Richardson GCI calculation."""
    report = AsmeVv20Verifier.evaluate_3grid_richardson(
        f1=req.f1_fine,
        f2=req.f2_medium,
        f3=req.f3_coarse,
        r21=req.refinement_ratio,
        r32=req.refinement_ratio,
        metric_name=req.metric_name,
    )
    return report.to_dict()


@router.post("/ready")
def post_ready(req: ReadyRequest) -> Dict[str, Any]:
    """Executes ASTM F3269-21 RTA packaging, human safety card, and Ed25519 signing."""
    packager = RtaAirworthinessPackager()
    card = packager.generate_approval_card(
        action_type=req.action_type,
        target_system=req.target_name,
        plain_summary=req.summary,
        load_factor_g=1.0,
    )
    if req.auto_approve:
        card.approve("FLIGHT_OPERATIONS_DIRECTOR")

    pkg = packager.package_flight_release(
        target_name=req.target_name,
        merkle_root=req.merkle_root,
        is_asme_vv20_verified=req.is_asme_vv20_verified,
        approved_cards=[card],
    )
    return pkg.to_dict()


@router.post("/pipeline")
def post_pipeline(req: PipelineRequest) -> Dict[str, Any]:
    """Executes the complete 4-step loop end-to-end."""
    if req.preset.lower() in ["naca4412", "aero"]:
        return run_naca4412_surrogate_pipeline(auto_approve=req.auto_approve)
    elif req.preset.lower() in ["spadex", "orbital"]:
        return run_spadex_eclipse_docking_pipeline(auto_approve=req.auto_approve)
    raise HTTPException(status_code=400, detail=f"Unsupported pipeline preset: {req.preset}")


# ─── CAD, MESHING, HIL & SPACEBORNE EDGE EXTENSIONS ───

class CadInspectRequest(BaseModel):
    name: Optional[str] = "TRIBAL_TACTICAL_UAV"
    filename: Optional[str] = None
    span: Optional[float] = None
    root_chord: Optional[float] = None
    tip_chord: Optional[float] = None
    raw_ascii_stl: Optional[str] = None
    use_preset_uav: bool = True


class MesherRequest(BaseModel):
    geometry_name: Optional[str] = "TRIBAL_TACTICAL_UAV"
    cad_filename: Optional[str] = None
    characteristic_length: Optional[float] = None
    chord_m: Optional[float] = None
    u_inf_mps: Optional[float] = None
    freestream_velocity: Optional[float] = None
    target_y_plus: float = 0.95
    grid_ratio: Optional[float] = None
    refinement_ratio: Optional[float] = None


class HilStepRequest(BaseModel):
    dt_sec: float = 0.01
    steps: Optional[int] = 1
    target_roll_deg: Optional[float] = 0.0
    target_pitch_deg: Optional[float] = 0.0


class HilInjectFaultRequest(BaseModel):
    fault_mode: Optional[str] = None
    failure_mode: Optional[str] = None
    magnitude: float = 18.0


class TmrEvaluateRequest(BaseModel):
    alpha_deg: Optional[float] = 4.0
    inject_seu_channel: Optional[int] = None
    inject_bitflip_channel: Optional[int] = None
    test_vector: Optional[List[float]] = None


class AutopilotExportRequest(BaseModel):
    airframe_name: Optional[str] = "TRIBAL_TACTICAL_UAV"
    vehicle_name: Optional[str] = None
    mass_kg: float = 12.5
    span_m: float = 2.4
    chord_m: float = 0.35
    v_cruise_mps: Optional[float] = None
    cruise_airspeed_mps: Optional[float] = None
    cl_alpha: Optional[float] = None
    cm_alpha: Optional[float] = None
    stability_derivatives: Optional[Dict[str, float]] = None


@router.post("/cad/inspect-stl")
def post_inspect_stl(req: CadInspectRequest) -> Dict[str, Any]:
    """Parses 3D surface STL, calculates MAC, planform area, aspect ratio, and sweep."""
    filename = req.filename or req.name or "uav_wing.stl"
    if req.raw_ascii_stl:
        metrics = CadGeometryEngine.parse_stl_ascii(req.raw_ascii_stl, name=filename)
    else:
        sample_bytes = CadGeometryEngine.generate_sample_uav_wing_stl(
            span=req.span or 2.4,
            root_chord=req.root_chord or 0.45,
            tip_chord=req.tip_chord or 0.22,
        )
        engine = CadGeometryEngine()
        metrics = engine.inspect_stl_bytes(sample_bytes, filename=filename)

    geom_dict = metrics.to_dict()
    geom_dict["span_m"] = metrics.span_b_m
    return {
        "status": "SUCCESS",
        "geometry": geom_dict,
        **geom_dict,
    }


@router.post("/mesher/generate-asme-grid")
def post_generate_asme_grid(req: MesherRequest) -> Dict[str, Any]:
    """Synthesizes ASME V&V 20 3-level grid hierarchy with prism inflation (y+ < 1.0)."""
    cad_name = req.cad_filename or req.geometry_name or "uav_wing.stl"
    chord = req.characteristic_length or req.chord_m or 1.0
    u_inf = req.freestream_velocity or req.u_inf_mps or 60.0
    ratio = req.refinement_ratio or req.grid_ratio or 1.414

    mesher = AutomatedMesher()
    grid_suite = mesher.generate_asme_vv20_grid_suite(
        cad_filename=cad_name,
        characteristic_length=chord,
        target_y_plus=req.target_y_plus,
        freestream_velocity=u_inf,
        refinement_ratio=ratio,
    )
    snappy = mesher.generate_openfoam_snappy_hex_mesh_dict(grid_suite)
    su2_cfg = mesher.generate_su2_config(grid_suite)

    suite_dict = grid_suite.to_dict()
    return {
        "status": "SUCCESS",
        "asme_vv20_compliant": grid_suite.asme_vv20_compliant,
        "grids": [
            {
                "level": g.level,
                "grid_index": g.grid_index,
                "cell_size_m": g.cell_size_m,
                "estimated_cells": g.estimated_cells,
                "y_plus": g.y_plus,
            }
            for g in grid_suite.grids
        ],
        "snappy_hex_mesh_dict": snappy,
        "su2_cfg": su2_cfg,
        "openfoam_snappy_dict": snappy,
        "su2_mesh_config": su2_cfg,
        **suite_dict,
    }


@router.post("/hil/step-telemetry")
def post_hil_step(req: HilStepRequest) -> Dict[str, Any]:
    """Steps the real-time 100 Hz Hardware-in-the-Loop simulation cycle."""
    steps = req.steps or 1
    target_roll = req.target_roll_deg or 0.0
    target_pitch = req.target_pitch_deg or 0.0
    for _ in range(steps):
        hil_bridge_singleton.step(target_roll_deg=target_roll, target_pitch_deg=target_pitch)
    frame = hil_bridge_singleton.step_simulation_cycle(dt=req.dt_sec)
    frame_dict = frame.to_dict()
    return {
        "status": "SUCCESS",
        "telemetry": frame_dict,
        **frame_dict,
    }


@router.post("/hil/inject-failure")
def post_hil_inject_failure(req: HilInjectFaultRequest) -> Dict[str, Any]:
    """Injects or clears flight hardware fault into the active HIL bridge."""
    mode_str = req.failure_mode or req.fault_mode or "NOMINAL"
    f_mode = getattr(HilFailureMode, mode_str, mode_str)
    hil_bridge_singleton.inject_failure(f_mode, magnitude=req.magnitude)
    active_str = str(hil_bridge_singleton.status.active_failure)
    return {
        "status": "INJECTED",
        "active_failure": active_str,
        "active_fault": hil_bridge_singleton.active_fault,
    }


@router.post("/space/tmr-evaluate")
def post_tmr_evaluate(req: TmrEvaluateRequest) -> Dict[str, Any]:
    """Executes on-orbit Triple Modular Redundancy (TMR) evaluation with AdaSkip pruning."""
    ch = req.inject_bitflip_channel if req.inject_bitflip_channel is not None else req.inject_seu_channel
    if req.test_vector is not None:
        voted_vec, seu_detected = tmr_exec_singleton.evaluate_with_tmr(
            test_state=req.test_vector,
            inject_bitflip_channel=ch,
        )
        return {
            "status": "SUCCESS",
            "seu_detected": seu_detected,
            "voted_vector": voted_vec,
            "seu_events_detected": tmr_exec_singleton.seu_events_detected,
        }
    else:
        res = tmr_exec_singleton.evaluate_with_tmr(
            alpha_deg=req.alpha_deg or 4.0,
            inject_seu_channel=ch,
        )
        res_dict = res.to_dict()
        res_dict["status"] = "SUCCESS"
        res_dict["seu_detected"] = res.seu_fault_detected
        res_dict["voted_vector"] = [res.voted_consensus_value]
        return res_dict


@router.post("/export/autopilot")
def post_export_autopilot(req: AutopilotExportRequest) -> Dict[str, Any]:
    """Synthesizes ready-to-flash ArduPilot .param and PX4 mixer configurations."""
    v_name = req.vehicle_name or req.airframe_name or "TRIBAL_TACTICAL_UAV"
    v_cruise = req.cruise_airspeed_mps or req.v_cruise_mps or 28.0
    derivs = req.stability_derivatives or {}
    cl_a = req.cl_alpha or derivs.get("cl_alpha", derivs.get("CL_alpha", 5.85))
    cm_a = req.cm_alpha or derivs.get("cm_alpha", derivs.get("Cm_alpha", -0.62))

    pkg = AutopilotHardwareExporter.generate_autopilot_package(
        airframe_name=v_name,
        mass_kg=req.mass_kg,
        span_m=req.span_m,
        chord_m=req.chord_m,
        v_cruise_mps=v_cruise,
        cl_alpha=cl_a,
        cm_alpha=cm_a,
    )
    return {
        "status": "SUCCESS",
        "ardupilot_param": pkg.ardupilot_param_text,
        "px4_mixer_toml": pkg.px4_mixer_text,
        "c_header": pkg.embedded_c_header_text,
        **pkg.to_dict(),
    }


