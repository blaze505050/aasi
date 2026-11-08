"""
Unit tests for Stage 29: Zero-Trust Post-Quantum Spacecraft Bus Security.
Verifies CRYSTALS-Kyber-1024, CRYSTALS-Dilithium-5, CCSDS anti-replay firewall,
and REST API endpoints.
"""

import pytest
from starlette.testclient import TestClient

from aasi_aero_fno.post_quantum_bus_security import (
    Kyber1024Engine,
    Dilithium5Engine,
    SpacecraftZeroTrustBus,
    TelecommandAction,
    BusThreatType,
    run_post_quantum_bus_audit,
)
from backend.main import app

client = TestClient(app)


def test_kyber1024_key_encapsulation_agreement():
    """Verifies that Kyber-1024 key encapsulation and decapsulation establish identical secrets."""
    kyber = Kyber1024Engine(seed=b"TEST_KYBER_SEED_1024_AASI")
    pk, sk = kyber.generate_keypair()

    assert pk["algorithm"] == "CRYSTALS-Kyber-1024"
    assert pk["k"] == 4
    assert pk["q"] == 3329

    ct, shared_secret_sender = kyber.encapsulate(pk)
    assert ct["size_bytes"] > 0
    assert len(shared_secret_sender) == 32

    shared_secret_receiver = kyber.decapsulate(ct, sk)
    assert shared_secret_sender == shared_secret_receiver


def test_dilithium5_telecommand_digital_signature():
    """Verifies Dilithium-5 digital signature validity and rejection of tampered messages."""
    dil = Dilithium5Engine(seed=b"TEST_DILITHIUM_SEED_5_AASI")
    vk, sk = dil.generate_keypair()

    assert vk["algorithm"] == "CRYSTALS-Dilithium-5"
    assert vk["matrix_rows"] == 8

    tc_payload = b"CCSDS_TC:APOGEE_MANEUVER_DELTA_V_0.75_MPS"
    signature = dil.sign_telecommand(tc_payload, sk)

    # Legitimate signature must pass
    assert dil.verify_telecommand(tc_payload, signature, vk) is True

    # Tampered key_id must be rejected
    tampered_sig = dict(signature)
    tampered_sig["key_id"] = "ROGUE_SAT_KEY"
    assert dil.verify_telecommand(tc_payload, tampered_sig, vk) is False

    # Tampered challenge hash must be rejected
    tampered_hash_sig = dict(signature)
    tampered_hash_sig["challenge_hash"] = "0" * 32  # Invalid length
    assert dil.verify_telecommand(tc_payload, tampered_hash_sig, vk) is False


def test_spacecraft_bus_zero_trust_firewall_defense():
    """Verifies anti-replay sliding window and malicious telecommand rejection."""
    bus = SpacecraftZeroTrustBus(spacecraft_id=0x2A4, processor_type="BAE_RAD750_133MHZ")
    bus.establish_pqc_session()

    # 1. Benign valid command
    valid_frame = bus.assemble_telecommand(
        action=TelecommandAction.ORBIT_MAINTENANCE_BURN,
        seq_count=1005,
        params={"delta_v_mps": 0.3},
        threat_type=BusThreatType.NO_THREAT_BENIGN,
    )
    res_valid = bus.process_telecommand_frame(valid_frame)
    assert res_valid.is_authenticated is True
    assert res_valid.bus_state == "ACCEPTED_AND_DISPATCHED"

    # 2. Replay attack: resubmitting sequence 1005 must be rejected
    res_replay = bus.process_telecommand_frame(valid_frame)
    assert res_replay.is_authenticated is False
    assert res_replay.threat_detected == BusThreatType.REPLAY_ATTACK
    assert res_replay.bus_state == "FIREWALL_REJECTED"

    # 3. Unauthorized hostile de-orbit injection
    hostile_frame = bus.assemble_telecommand(
        action=TelecommandAction.UNAUTHORIZED_DEORBIT_BURN,
        seq_count=1006,
        params={"delta_v_mps": -500.0},
        threat_type=BusThreatType.UNAUTHORIZED_COMMAND_INJECTION,
    )
    res_hostile = bus.process_telecommand_frame(hostile_frame)
    assert res_hostile.is_authenticated is False
    assert res_hostile.bus_state == "FIREWALL_REJECTED"


def test_pqc_bus_api_endpoints():
    """Verifies FastAPI REST endpoints for PQC bus security."""
    # Test presets
    resp_presets = client.get("/api/v1/pqc-bus/presets")
    assert resp_presets.status_code == 200
    presets = resp_presets.json()["data"]
    assert "RAD750_GAGANYAAN_ORBITER" in presets

    # Test status
    resp_status = client.get("/api/v1/pqc-bus/status")
    assert resp_status.status_code == 200
    assert resp_status.json()["standards"]["security_margin_bits"] == 256

    # Test audit simulation
    resp_audit = client.post(
        "/api/v1/pqc-bus/audit",
        json={
            "spacecraft_id": 676,
            "processor_type": "BAE_RAD750_133MHZ",
            "total_frames": 6,
            "inject_threats": True,
        },
    )
    assert resp_audit.status_code == 200
    audit = resp_audit.json()["data"]
    assert audit["audit_summary"]["firewall_effectiveness_percent"] == 100.0
    assert audit["audit_summary"]["threats_prevented"] >= 2
    assert len(audit["frame_telemetry"]) == 6
