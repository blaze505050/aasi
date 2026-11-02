"""
Unit tests for Module 4: aasi-netra-catfm.
Verifies Project NETRA SSA debris conjunction screening & CAM delta-v calculations,
AAI C-ATFM national airspace flow optimization & Ground Delay Programs,
and BlazeWatch MHA dual-stream disaster & counter-UAS interceptor tracking.
"""

import math
import pytest
from fastapi.testclient import TestClient

from aasi_netra_catfm import (
    ProjectNetraConjunctionEngine,
    DebrisObjectCatalog,
    ConjunctionAlert,
    CollisionAvoidanceManeuver,
    AAICATFMOptimizer,
    AirportNode,
    AirspaceFlowStatus,
    GroundDelayProgram,
    BlazeWatchSecurityIntelligence,
    DisasterHotspotAlert,
    CounterUASTracker,
)

from api_server import app


class TestAASISovereignNetraCATFM:
    """Test suite for NETRA SSA, AAI C-ATFM, and BlazeWatch security hub."""

    def test_netra_2d_encounter_probability(self):
        """Verifies Foster 2D encounter collision probability calculation."""
        engine = ProjectNetraConjunctionEngine()

        # Near direct collision: miss distance 5 meters
        pc_high = engine.compute_2d_encounter_probability(
            miss_radial_m=3.0,
            miss_cross_m=4.0,
            combined_hard_body_radius_m=3.5,
            sigma_radial_m=40.0,
            sigma_cross_m=80.0,
        )
        assert pc_high > 1e-4

        # Far encounter: miss distance 5000 meters
        pc_low = engine.compute_2d_encounter_probability(
            miss_radial_m=3000.0,
            miss_cross_m=4000.0,
            combined_hard_body_radius_m=3.5,
            sigma_radial_m=40.0,
            sigma_cross_m=80.0,
        )
        assert pc_low < 1e-10

    def test_netra_screening_and_cam_optimization(self):
        """Verifies orbital screening against catalog and optimal CAM burn generation."""
        engine = ProjectNetraConjunctionEngine()
        alerts = engine.screen_asset_trajectory(
            asset_name="SpaDeX-SDX01",
            asset_altitude_km=470.0,
        )

        assert len(alerts) > 0
        for alert in alerts:
            assert alert.primary_asset_name == "SpaDeX-SDX01"
            assert alert.alert_level in ["GREEN", "YELLOW", "RED"]
            if alert.alert_level in ["YELLOW", "RED"]:
                assert alert.recommended_cam_burn is not None
                assert "delta_v_mps" in alert.recommended_cam_burn
                assert alert.recommended_cam_burn["delta_v_mps"] > 0.0

        # Verify CAM calculation specifically
        cam = engine.compute_optimal_cam(
            asset_name="SpaDeX-SDX01",
            current_miss_m=280.0,
            time_to_ca_s=7200.0,
            target_clearance_m=2500.0,
        )
        assert cam.burn_direction == "PROGRADE"
        assert cam.delta_v_mps >= 0.05
        assert cam.propellant_cost_kg > 0.0
        assert cam.projected_post_burn_miss_m >= 2500.0

    def test_aai_catfm_airspace_flow(self):
        """Verifies AAI C-ATFM network congestion and Ground Delay Programs."""
        optimizer = AAICATFMOptimizer()
        status = optimizer.evaluate_network_flow()

        assert status.total_national_demand > 0
        assert status.total_national_capacity > 0
        assert 0.0 <= status.network_congestion_index <= 1.0
        assert len(status.airports) >= 6
        assert len(status.active_gdps) > 0

        # Check fuel and CO2 savings are positive
        for gdp in status.active_gdps:
            assert gdp.fuel_saved_metric_tons > 0.0
            assert gdp.co2_reduction_metric_tons > 0.0

    def test_blazewatch_disaster_and_counter_uas(self):
        """Verifies BlazeWatch dual-stream alerts and Counter-UAS interceptor tracking."""
        bw = BlazeWatchSecurityIntelligence()
        alerts = bw.scan_homeland_threats()

        assert len(alerts) >= 3
        # Check benchmarks from strategy plan
        for alert in alerts:
            assert alert.lstm_thermal_confidence >= 0.98
            assert alert.bert_nlp_verification_score >= 0.99
            assert alert.crisis_category in [
                "WILDFIRE",
                "INDUSTRIAL_REFINERY_FLARE",
                "FLASH_FLOOD_RAIN",
                "LANDSLIDE",
            ]

        # Verify Counter-UAS proportional navigation interceptor
        target_pos = (1500.0, 900.0, -200.0)
        target_vel = (-30.0, -12.0, 3.0)
        uas_track = bw.track_counter_uas_interceptor(target_pos, target_vel)

        assert uas_track.target_type == "ROGUE_DRONE"
        assert uas_track.distance_m > 1000.0
        assert uas_track.los_rate_rad_s > 0.0
        assert "Seeker Lock Confirmed" in uas_track.interceptor_guidance_command

    def test_sovereign_fastapi_rest_endpoints(self):
        """Verifies unified FastAPI REST endpoints for the sovereign platform."""
        client = TestClient(app)

        # 1. Constitution & ASTM F3269-21 RTA Evaluation
        r_rta = client.post(
            "/api/v2/constitution/evaluate",
            json={
                "subsystem": "GNC",
                "action_type": "THRUSTER_BURN",
                "parameters": {"thrust_n": 10.0, "duration_ms": 40.0},
                "rationale": "V-bar closing maneuver",
            },
        )
        assert r_rta.status_code == 200
        data_rta = r_rta.json()
        assert "authorized" in data_rta
        assert "signature_hex" in data_rta
        assert "merkle_root_hash" in data_rta

        # 2. Aero-FNO Aerodynamic & Aeroelastic Evaluation
        r_aero = client.post(
            "/api/v2/aero/evaluate",
            json={"airfoil": "NACA 4412", "alpha_deg": 4.0, "reynolds": 1.5e6, "mach": 0.18},
        )
        assert r_aero.status_code == 200
        data_aero = r_aero.json()
        assert "flow_evaluation" in data_aero
        assert "aeroelastic_flutter_recovery" in data_aero

        # 3. Orbital GNC SpaDeX Docking Simulation
        r_dock = client.post(
            "/api/v2/gnc/docking-trajectory",
            json={"vehicle_preset": "SPADEX", "initial_distance_m": 25.0, "max_steps": 10},
        )
        assert r_dock.status_code == 200
        data_dock = r_dock.json()
        assert data_dock["vehicle"] == "ISRO SpaDeX (SDX01 Chaser / SDX02 Target)"
        assert len(data_dock["trajectory"]) > 0

        # 4. NETRA SSA Screening
        r_netra = client.get("/api/v2/netra/alerts")
        assert r_netra.status_code == 200
        data_netra = r_netra.json()
        assert "conjunctions" in data_netra
        assert len(data_netra["conjunctions"]) > 0

        # 5. AAI C-ATFM Airspace Flow
        r_catfm = client.get("/api/v2/catfm/status")
        assert r_catfm.status_code == 200
        data_catfm = r_catfm.json()
        assert "network_congestion_index" in data_catfm
        assert len(data_catfm["airports"]) >= 6

        # 6. BlazeWatch Homeland Security
        r_bw = client.get("/api/v2/blazewatch/threats")
        assert r_bw.status_code == 200
        data_bw = r_bw.json()
        assert "disaster_alerts" in data_bw
        assert len(data_bw["disaster_alerts"]) >= 3
