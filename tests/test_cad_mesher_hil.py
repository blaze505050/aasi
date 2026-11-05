"""
Verification Test Suite for Aero-CAD Ingestion, Automated Meshing,
HIL/SITL Flight Bridge, Spaceborne AdaSkip/TMR, and Autopilot Exporter.
"""

import sys
import os
import math
import struct
import pytest
from fastapi.testclient import TestClient

# Ensure modules are discoverable
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE_DIR, "aasi-craft"))
sys.path.insert(0, os.path.join(BASE_DIR, "aasi-constitution-rta"))
sys.path.insert(0, os.path.join(BASE_DIR, "aasi-aero-fno"))
sys.path.insert(0, os.path.join(BASE_DIR, "aasi-orbital-gnc"))
sys.path.insert(0, os.path.join(BASE_DIR, "aasi-netra-catfm"))
sys.path.insert(0, BASE_DIR)

from aasi_craft.cad.geometry_engine import CadGeometryEngine, generate_sample_uav_wing_stl
from aasi_craft.mesher.automated_mesher import AutomatedMesher
from aasi_orbital_gnc.hil_bridge import HilFlightBridge, HilFailureMode
from aasi_aero_fno.adaskip_tmr import SpaceborneEdgeAeroSurrogate, TmrRadiationExecutive
from aasi_craft.exporters.autopilot_exporter import AutopilotHardwareExporter
from backend.main import app

client = TestClient(app)


# ---------------------------------------------------------------------------
# Pillar 1: CAD & Meshing Tests
# ---------------------------------------------------------------------------

def test_cad_stl_parsing_and_metrics():
    """Verifies binary STL parsing and wing planform/aerodynamic calculations."""
    engine = CadGeometryEngine()
    stl_bytes = generate_sample_uav_wing_stl(span=2.4, root_chord=0.45, tip_chord=0.22)
    
    geom = engine.inspect_stl_bytes(stl_bytes, filename="test_uav_wing.stl")
    assert geom.triangle_count >= 12
    assert geom.span == pytest.approx(2.4, rel=1e-2)
    assert geom.root_chord == pytest.approx(0.45, rel=1e-2)
    assert geom.tip_chord > 0.10
    assert geom.taper_ratio > 0.30
    assert geom.planform_area > 0.5
    assert geom.aspect_ratio > 3.0
    assert geom.mean_aerodynamic_chord > 0.25
    assert geom.wetted_area > geom.planform_area


def test_cad_ascii_stl_parsing():
    """Verifies parsing of ASCII formatted STL files."""
    ascii_stl = """solid simple_triangle
facet normal 0.0 0.0 1.0
  outer loop
    vertex 0.0 0.0 0.0
    vertex 1.0 0.0 0.0
    vertex 0.5 1.0 0.0
  endloop
endfacet
endsolid simple_triangle
"""
    engine = CadGeometryEngine()
    geom = engine.inspect_stl_bytes(ascii_stl.encode("utf-8"), filename="simple.stl")
    assert geom.triangle_count == 1
    assert geom.wetted_area == pytest.approx(0.5, rel=1e-2)


def test_automated_mesher_asme_vv20_compliance():
    """Verifies boundary layer inflation calculator and ASME V&V 20 grid hierarchy."""
    mesher = AutomatedMesher()
    grid_suite = mesher.generate_asme_vv20_grid_suite(
        cad_filename="uav_wing.stl",
        characteristic_length=0.35,
        target_y_plus=1.0,
        freestream_velocity=35.0,
        refinement_ratio=math.sqrt(2.0),
    )

    assert grid_suite.target_y_plus == 1.0
    assert grid_suite.refinement_ratio >= 1.30
    assert grid_suite.first_cell_height_m > 0
    assert grid_suite.first_cell_height_m < 5e-5  # For 35 m/s, y+ 1.0 is ~1.8e-5 m
    assert grid_suite.prism_layer_count >= 15
    assert 1.15 <= grid_suite.prism_growth_ratio <= 1.25
    assert grid_suite.asme_vv20_compliant is True

    # Check the 3-level grid hierarchy
    assert len(grid_suite.grids) == 3
    fine = grid_suite.grids[0]
    medium = grid_suite.grids[1]
    coarse = grid_suite.grids[2]

    assert fine.level == "Fine (G1)"
    assert medium.level == "Medium (G2)"
    assert coarse.level == "Coarse (G3)"
    assert fine.estimated_cells > medium.estimated_cells > coarse.estimated_cells


def test_mesher_deck_generators():
    """Verifies that OpenFOAM snappyHexMesh and SU2 configuration files are generated correctly."""
    mesher = AutomatedMesher()
    grid_suite = mesher.generate_asme_vv20_grid_suite("recon_drone.stl", characteristic_length=0.4)
    
    snappy = mesher.generate_openfoam_snappy_hex_mesh_dict(grid_suite)
    assert "FoamFile" in snappy
    assert "snappyHexMeshDict" in snappy
    assert "nSurfaceLayers" in snappy
    assert "recon_drone.stl" in snappy

    su2_cfg = mesher.generate_su2_config(grid_suite, mach=0.15, reynolds=850000.0)
    assert "SOLVER= RANS" in su2_cfg
    assert "KIND_TURB_MODEL= SA" in su2_cfg
    assert "MACH_NUMBER=" in su2_cfg


# ---------------------------------------------------------------------------
# Pillar 2: HIL / SITL Flight Bridge Tests
# ---------------------------------------------------------------------------

def test_hil_mavlink_v2_encoding_and_decoding():
    """Verifies MAVLink v2 binary packet framing, CRC, and payload extraction."""
    bridge = HilFlightBridge()
    packet = bridge.encode_mavlink_v2_attitude(
        roll_rad=0.1,
        pitch_rad=-0.05,
        yaw_rad=1.57,
        rollspeed=0.01,
        pitchspeed=-0.02,
        yawspeed=0.03,
    )
    
    # Check packet header
    assert packet[0] == 0xFD  # MAVLink v2 STX magic
    assert packet[1] == 28    # Payload length for ATTITUDE message
    assert len(packet) == 10 + 28 + 2  # Header (10) + Payload (28) + Checksum (2) = 40 bytes

    # Decode packet
    decoded = bridge.decode_mavlink_v2_packet(packet)
    assert decoded["msg_id"] == 30  # ATTITUDE
    assert decoded["msg_name"] == "ATTITUDE"
    assert decoded["payload"]["roll_rad"] == pytest.approx(0.1, abs=1e-4)
    assert decoded["payload"]["pitch_rad"] == pytest.approx(-0.05, abs=1e-4)
    assert decoded["payload"]["yaw_rad"] == pytest.approx(1.57, abs=1e-4)


def test_hil_closed_loop_failure_injection_and_recovery():
    """Verifies failure injection and active AIDI adaptive stabilization."""
    bridge = HilFlightBridge(rate_hz=100.0)
    
    # Run 50 steps of nominal flight
    for _ in range(50):
        bridge.step(target_roll_deg=0.0, target_pitch_deg=2.0)
    
    assert bridge.status.active_failure == HilFailureMode.NOMINAL
    assert bridge.status.recovery_active is False

    # Inject Aileron Jam (+18 degrees deflection)
    bridge.inject_failure(HilFailureMode.ACTUATOR_JAM_AILERON, magnitude=18.0)
    assert bridge.status.active_failure == HilFailureMode.ACTUATOR_JAM_AILERON

    # Step closed-loop simulation under failure
    for _ in range(100):  # 1.0 second simulation
        bridge.step(target_roll_deg=0.0, target_pitch_deg=2.0)

    # Adaptive Fault-Tolerant Law must engage and keep roll angle bounded
    assert bridge.status.recovery_active is True
    assert bridge.status.recovery_latency_ms < 350.0
    # Roll error should be actively counter-acted by differential surfaces
    assert abs(bridge.status.attitude_deg["roll"]) < 25.0


# ---------------------------------------------------------------------------
# Pillar 4: Spaceborne Edge AI & TMR SEU Protection Tests
# ---------------------------------------------------------------------------

def test_spaceborne_edge_surrogate_adaskip():
    """Verifies AdaSkip dynamic layer skipping in quasi-steady flow regimes."""
    model = SpaceborneEdgeAeroSurrogate(in_channels=3, out_channels=3, modes=8, width=16)
    
    # 1. Quasi-steady condition: low spatial gradient (should trigger skip)
    x_steady = [0.1 + 0.001 * math.sin(i * 0.1) for i in range(64 * 3)]
    out_steady, metrics_steady = model.forward_with_adaskip(x_steady, gradient_threshold=0.05)
    
    assert len(out_steady) == 64 * 3
    assert metrics_steady["skipped_blocks"] >= 2  # Blocks 2 & 3 skipped
    assert metrics_steady["computation_saved_pct"] >= 45.0

    # 2. High-gradient condition: shock/wake (should NOT skip)
    x_unsteady = [1.0 if i % 2 == 0 else -1.0 for i in range(64 * 3)]
    out_unsteady, metrics_unsteady = model.forward_with_adaskip(x_unsteady, gradient_threshold=0.05)
    assert metrics_unsteady["skipped_blocks"] == 0
    assert metrics_unsteady["computation_saved_pct"] == 0.0


def test_tmr_radiation_executive_seu_masking():
    """Verifies Triple Modular Redundancy (TMR) masking of cosmic ray bit flips."""
    tmr = TmrRadiationExecutive()
    test_state = [100.5, -24.3, 12.0, 0.05, 0.99]
    
    # Injected SEU into Channel 2
    voted_output, seu_detected = tmr.evaluate_with_tmr(test_state, inject_bitflip_channel=2)
    
    # Output must match channel 1 & 3 exactly (2-of-3 majority vote)
    assert seu_detected is True
    assert tmr.seu_events_detected == 1
    assert voted_output[0] == pytest.approx(100.5, abs=1e-5)
    assert voted_output[1] == pytest.approx(-24.3, abs=1e-5)


# ---------------------------------------------------------------------------
# Pillar 5: Commercial Autopilot Exporters Tests
# ---------------------------------------------------------------------------

def test_autopilot_exporter_ardupilot_and_px4():
    """Verifies automated synthesis of tuned PID gains and flight config files."""
    exporter = AutopilotHardwareExporter()
    
    # Aerodynamic stability derivatives
    derivatives = {
        "CL_alpha": 4.8,
        "Cm_alpha": -0.65,
        "Cl_beta": -0.09,
        "Cn_beta": 0.12,
        "CD0": 0.024,
    }

    # ArduPilot parameter file
    param_text = exporter.generate_ardupilot_param(
        vehicle_name="AASI_UAV_01",
        stability_derivatives=derivatives,
        cruise_airspeed_mps=28.0,
    )
    assert "AASI Sovereign Aerospace" in param_text
    assert "RLL2SRV_P" in param_text
    assert "PTCH2SRV_P" in param_text
    assert "SCALING_SPEED,28.0" in param_text

    # PX4 Mixer airframe configuration
    px4_text = exporter.generate_px4_mixer_config(
        vehicle_name="AASI_UAV_01",
        stability_derivatives=derivatives,
    )
    assert "[airframe]" in px4_text
    assert "name = \"AASI_UAV_01\"" in px4_text
    assert "actuator_1_roll" in px4_text
    assert "actuator_2_pitch" in px4_text

    # ANSI C flight table header
    c_header = exporter.generate_c_flight_table_header(
        vehicle_name="AASI_UAV_01",
        stability_derivatives=derivatives,
    )
    assert "#ifndef AASI_AERO_TABLE_H_" in c_header
    assert "AASI_AERO_CL_ALPHA" in c_header
    assert "AASI_PID_PITCH_P" in c_header


# ---------------------------------------------------------------------------
# REST API Endpoints Integration Tests
# ---------------------------------------------------------------------------

def test_api_craft_cad_and_mesher():
    """Verifies REST endpoints for CAD inspection and ASME meshing."""
    # 1. CAD inspection endpoint
    response = client.post("/api/v2/craft/cad/inspect-stl", json={
        "filename": "uav_wing.stl",
        "span": 2.2,
        "root_chord": 0.40,
        "tip_chord": 0.20,
    })
    assert response.status_code == 200
    cad_data = response.json()
    assert cad_data["status"] == "SUCCESS"
    assert cad_data["geometry"]["span_m"] == 2.2
    assert cad_data["geometry"]["mean_aerodynamic_chord_m"] > 0.2

    # 2. Mesher endpoint
    response = client.post("/api/v2/craft/mesher/generate-asme-grid", json={
        "cad_filename": "uav_wing.stl",
        "characteristic_length": 0.35,
        "target_y_plus": 1.0,
        "freestream_velocity": 30.0,
    })
    assert response.status_code == 200
    mesh_data = response.json()
    assert mesh_data["status"] == "SUCCESS"
    assert mesh_data["asme_vv20_compliant"] is True
    assert len(mesh_data["grids"]) == 3
    assert "FoamFile" in mesh_data["snappy_hex_mesh_dict"]
    assert "SOLVER= RANS" in mesh_data["su2_cfg"]


def test_api_craft_hil_and_space_and_export():
    """Verifies REST endpoints for HIL stepping, failure injection, TMR, and Autopilot export."""
    # 1. HIL Step
    response = client.post("/api/v2/craft/hil/step-telemetry", json={
        "steps": 5,
        "target_roll_deg": 5.0,
        "target_pitch_deg": 3.0,
    })
    assert response.status_code == 200
    hil_data = response.json()
    assert hil_data["status"] == "SUCCESS"
    assert "telemetry" in hil_data

    # 2. HIL Failure Injection
    response = client.post("/api/v2/craft/hil/inject-failure", json={
        "failure_mode": "ACTUATOR_JAM_AILERON",
        "magnitude": 15.0,
    })
    assert response.status_code == 200
    inj_data = response.json()
    assert inj_data["status"] == "INJECTED"
    assert inj_data["active_failure"] == "ACTUATOR_JAM_AILERON"

    # 3. Spaceborne TMR evaluation
    response = client.post("/api/v2/craft/space/tmr-evaluate", json={
        "test_vector": [1.0, 2.0, 3.0],
        "inject_bitflip_channel": 1,
    })
    assert response.status_code == 200
    tmr_data = response.json()
    assert tmr_data["seu_detected"] is True
    assert tmr_data["voted_vector"] == [1.0, 2.0, 3.0]

    # 4. Autopilot Export
    response = client.post("/api/v2/craft/export/autopilot", json={
        "vehicle_name": "Sovereign_Surya_UAV",
        "stability_derivatives": {
            "CL_alpha": 4.6,
            "Cm_alpha": -0.58,
            "Cl_beta": -0.08,
            "Cn_beta": 0.11,
            "CD0": 0.022,
        },
        "cruise_airspeed_mps": 32.0,
    })
    assert response.status_code == 200
    export_data = response.json()
    assert export_data["status"] == "SUCCESS"
    assert "ardupilot_param" in export_data
    assert "px4_mixer_toml" in export_data
    assert "c_header" in export_data
