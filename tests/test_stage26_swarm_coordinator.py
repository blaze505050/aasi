"""
Unit tests for Stage 26: Autonomous Heterogeneous UAV Swarm Tactical Coordinator.
"""

import pytest
from starlette.testclient import TestClient

from aasi_aero_fno.swarm_tactical_coordinator import (
    UAVRole,
    SwarmFormation,
    compute_induced_drag_reduction,
    solve_cbf_collision_avoidance,
    verify_byzantine_fault_consensus,
    simulate_tactical_swarm_mission,
)
from backend.main import app

client = TestClient(app)


def test_induced_drag_reduction_v_formation():
    drag_red = compute_induced_drag_reduction(
        lateral_spacing_m=2.4,  # exactly 1 wingspan
        longitudinal_spacing_m=10.0,
        wing_span_m=2.4,
    )
    assert 12.0 <= drag_red <= 20.0

    drag_far = compute_induced_drag_reduction(
        lateral_spacing_m=20.0,
        longitudinal_spacing_m=10.0,
        wing_span_m=2.4,
    )
    assert drag_far < drag_red


def test_cbf_zero_collision_guarantee():
    res = simulate_tactical_swarm_mission(
        mission_id="PERIMETER_BASE_DEFENSE",
        formation_type=SwarmFormation.DEFENSIVE_RING,
        num_uavs=16,
        d_safe=10.0,
        byzantine_adversary_present=False,
        steps=40,
    )
    assert res["safety_guarantees"]["cbf_zero_collision_verified"] is True
    assert res["safety_guarantees"]["min_distance_observed_m"] >= 8.5
    assert res["executive_summary"]["collision_status"] == "ZERO_COLLISION_CBF_PROVEN"


def test_byzantine_fault_consensus():
    # 1. Resilient condition (2 faulty nodes < (18-1)//3 = 5)
    votes = [100.0 + i for i in range(18)]
    bft_resilient = verify_byzantine_fault_consensus(
        swarm_nodes_count=18,
        compromised_nodes=[2, 5],
        consensus_votes=votes,
    )
    assert bft_resilient["consensus_resilience_intact"] is True
    assert bft_resilient["consensus_status"] == "BYZANTINE_CONSENSUS_REACHED"

    # 2. Compromised condition (6 faulty nodes > 5)
    bft_compromised = verify_byzantine_fault_consensus(
        swarm_nodes_count=18,
        compromised_nodes=[1, 2, 3, 4, 5, 6],
        consensus_votes=votes,
    )
    assert bft_compromised["consensus_resilience_intact"] is False
    assert bft_compromised["consensus_status"] == "CONSENSUS_COMPROMISED_QUORUM_LOST"


def test_heterogeneous_roles_and_mission():
    res = simulate_tactical_swarm_mission(
        mission_id="INDIAN_AF_ALFAS_SWARM",
        formation_type=SwarmFormation.V_FORMATION,
        num_uavs=18,
        d_safe=12.0,
        byzantine_adversary_present=True,
        steps=30,
    )
    assert res["total_uavs"] == 18
    assert res["roles_breakdown"]["LEADER"] == 1
    assert res["roles_breakdown"]["SCOUT"] > 0
    assert res["roles_breakdown"]["KINETIC_STRIKE"] > 0
    assert len(res["trajectory_snapshots"]) > 0


def test_swarm_api_endpoints():
    # 1. Presets endpoint
    res_presets = client.get("/api/swarm/presets")
    assert res_presets.status_code == 200
    presets = res_presets.json()
    assert "INDIAN_AF_ALFAS_SWARM" in presets
    assert "PERIMETER_BASE_DEFENSE" in presets

    # 2. Status endpoint
    res_status = client.get("/api/swarm/status")
    assert res_status.status_code == 200
    status_data = res_status.json()
    assert status_data["status"] == "OPERATIONAL"
    assert status_data["cbf_safety_guarantee"] == "PROVABLE_QUADRATIC_PROGRAMMING"

    # 3. Simulate endpoint
    payload = {
        "mission_id": "INDIAN_AF_ALFAS_SWARM",
        "formation_type": "V_FORMATION",
        "num_uavs": 12,
        "d_safe": 10.0,
        "byzantine_adversary_present": False,
        "steps": 25,
    }
    res_sim = client.post("/api/swarm/simulate", json=payload)
    assert res_sim.status_code == 200
    sim_data = res_sim.json()
    assert "safety_guarantees" in sim_data
    assert "aerodynamics" in sim_data
    assert "byzantine_consensus" in sim_data
