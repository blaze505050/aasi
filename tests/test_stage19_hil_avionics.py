"""
Unit and Integration Tests for Stage 19: Hardware-in-the-Loop (HIL) 1000 Hz Avionics Testbed.
=============================================================================================
"""

import struct
import pytest
from fastapi.testclient import TestClient

from backend.main import app
from aasi_aero_fno.hil_avionics_testbed import (
    HILAvionicsTestbedEngine,
    HIL_SCENARIO_PRESETS,
    encode_mavlink_v2_hil_sensor,
    encode_can_aerospace_frame,
    calculate_crc16_mcrf4xx,
    ActuatorFaultType,
)


@pytest.fixture
def client():
    return TestClient(app)


def test_mavlink_v2_hil_sensor_encoding():
    """Validates binary MAVLink v2 protocol serialization and CRC16-MCRF4XX verification."""
    timestamp = 1250000  # 1.25s
    alpha = 5.25
    pitch = 4.80
    airspeed = 65.4
    nz = 1.05

    frame = encode_mavlink_v2_hil_sensor(
        timestamp_us=timestamp,
        alpha_deg=alpha,
        pitch_deg=pitch,
        airspeed_mps=airspeed,
        nz_g=nz,
        seq=42,
    )

    # Frame structure: 10 bytes header + 24 bytes payload + 2 bytes CRC = 36 bytes (or 35 depending on payload struct)
    assert len(frame) >= 34
    assert frame[0] == 0xFD, "MAVLink v2 magic byte must be 0xFD"

    # Verify CRC
    payload_and_header = frame[1:-2]
    expected_crc = calculate_crc16_mcrf4xx(payload_and_header)
    (frame_crc,) = struct.unpack("<H", frame[-2:])
    assert frame_crc == expected_crc, "MAVLink v2 frame CRC checksum must match"


def test_can_aerospace_frame_encoding():
    """Validates CAN-Aerospace / ARINC 825 8-byte frame packing and IEEE-754 payload fidelity."""
    node_id = 0x0C
    channel_id = 0x03
    message_type = 0x01
    val = 14.82

    frame = encode_can_aerospace_frame(
        node_id=node_id,
        channel_id=channel_id,
        message_type=message_type,
        data_float=val,
    )

    assert len(frame) == 8, "CAN-Aerospace frames must be exactly 8 bytes"
    assert frame[0] == node_id
    assert frame[1] == 0x05  # float32 data type identifier
    assert frame[2] == channel_id

    # Unpack float
    (unpacked_val,) = struct.unpack(">f", frame[4:8])
    assert pytest.approx(val, rel=1e-4) == unpacked_val


def test_hil_simulation_pixhawk6x_microburst():
    """Validates 1000 Hz hard real-time cycle execution and microburst gust recovery."""
    dossier = HILAvionicsTestbedEngine.run_hil_simulation(
        preset_key="PIXHAWK6X_AUTONOMOUS_TRANSITION",
        duration_seconds=1.0,
    )

    bm = dossier.benchmark
    assert bm.total_cycles_executed == 1000
    assert bm.nominal_loop_period_us == 1000.0
    assert bm.mean_latency_us < 10.0, "Mean loop latency must be < 10 us on microsecond plant"
    assert bm.max_latency_us < 15.0, "Worst-case latency must not exceed 15 us"
    assert bm.max_jitter_us < 5.0, "Jitter must remain strictly bounded"
    assert bm.deadline_misses == 0, "Zero deadline misses allowed in 1000 Hz hard real-time"
    assert bm.real_time_schedulability_ratio < 2.0, "CPU utilization under 2%"
    assert bm.fault_recovery_time_ms < 100.0, "Recovery within 100 ms"
    assert bm.hil_compliance_status == "CERTIFIED_HARD_REAL_TIME_1000HZ"
    assert len(bm.provenance_hash) == 64
    assert len(dossier.telemetry_samples) == 200  # 1000 / 5 subsampled


def test_hil_fault_recovery_stuck_actuator():
    """Verifies that CBF-QP RTA prevents envelope departure when actuator gets stuck at +18°."""
    dossier = HILAvionicsTestbedEngine.run_hil_simulation(
        preset_key="STM32H7_TRANSONIC_FLUTTER_GUARD",
        override_fault=ActuatorFaultType.STUCK_AT_DEFLECTION.value,
        duration_seconds=1.0,
    )

    alpha_max = 22.0
    telemetry = dossier.telemetry_samples

    # Verify envelope remained protected during full stuck-actuator fault
    for sample in telemetry:
        assert sample.alpha_deg <= alpha_max + 1.0, f"Alpha exceeded limit: {sample.alpha_deg} > {alpha_max}"

    # Verify RTA actively took over
    interventions = sum(1 for s in telemetry if s.rta_intervention)
    assert interventions > 0, "RTA must intervene to counter stuck actuator"


def test_api_hil_avionics_endpoints(client):
    """Verifies FastAPI endpoints for Stage 19 HIL avionics testbed."""
    # 1. Presets endpoint
    res_presets = client.get("/api/hil-avionics/presets")
    assert res_presets.status_code == 200
    presets = res_presets.json()
    assert "PIXHAWK6X_AUTONOMOUS_TRANSITION" in presets
    assert "ISRO_VIKRAM_O6_REENTRY_HIL" in presets
    assert "STM32H7_TRANSONIC_FLUTTER_GUARD" in presets

    # 2. Simulate endpoint
    payload = {
        "preset_key": "ISRO_VIKRAM_O6_REENTRY_HIL",
        "duration_seconds": 0.5,
    }
    res_sim = client.post("/api/hil-avionics/simulate", json=payload)
    assert res_sim.status_code == 200
    data = res_sim.json()

    assert data["preset_key"] == "ISRO_VIKRAM_O6_REENTRY_HIL"
    assert "benchmark" in data
    assert data["benchmark"]["total_cycles_executed"] == 500
    assert data["benchmark"]["deadline_misses"] == 0
    assert data["benchmark"]["hil_compliance_status"] == "CERTIFIED_HARD_REAL_TIME_1000HZ"
    assert len(data["telemetry_samples"]) == 100
