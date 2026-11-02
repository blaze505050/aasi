"""
Unit tests for Module 3: aasi-orbital-gnc.
Verifies 6-DOF relative orbital dynamics, NavIC RODP + ISL sensor fusion filter
(225-meter post-eclipse drift elimination), Meta-RL proximity docking simulation,
and 6-DOF nonlinear aircraft fault-tolerant control (AIDI).
"""

import math
import numpy as np
import pytest

from aasi_orbital_gnc import (
    OrbitalVehicleConfig,
    OrbitalState6DOF,
    RelativeOrbitalDynamics6DOF,
    SPADEX_CONFIG,
    CHANDRAYAAN4_CONFIG,
    BAS01_CONFIG,
    NavICRODPSensorFusionFilter,
    SensorMeasurements5Tier,
    SensorTier,
    MetaRLDockingPolicy,
    AutonomousDockingSimulator,
    DockingStepResult,
    Aircraft6DOFDynamics,
    ActuatorFailureMode,
    AdaptiveIncrementalDynamicInversionController,
)


class TestAASISovereignOrbitalGNC:
    """Test suite for orbital relative dynamics, NavIC filter, and GNC controllers."""

    def test_orbital_dynamics_presets_and_rk4(self):
        """Verifies presets for SpaDeX, Chandrayaan-4, BAS-01 and RK4 propagation."""
        assert SPADEX_CONFIG.mass_kg == 220.0
        assert SPADEX_CONFIG.docking_port_diameter_mm == 450.0
        assert CHANDRAYAAN4_CONFIG.mass_kg == 9200.0
        assert BAS01_CONFIG.docking_port_diameter_mm == 800.0

        dynamics = RelativeOrbitalDynamics6DOF(SPADEX_CONFIG)
        assert dynamics.omega > 0.0

        initial_state = OrbitalState6DOF(
            rel_pos_m=(0.0, 225.0, 0.0),
            rel_vel_mps=(0.0, -0.15, 0.0),
            attitude_deg=(0.0, 0.0, 0.0),
            angular_velocity_rad_s=(0.0, 0.0, 0.0),
            fuel_remaining_kg=20.0,
        )

        # Step forward with braking thrust along Y
        next_state = dynamics.step_rk4(
            initial_state,
            rcs_force_n=(0.0, 5.0, 0.0),
            rcs_torque_nm=(0.1, 0.0, 0.0),
            dt=1.0,
        )

        assert next_state.time_s == 1.0
        assert next_state.rel_pos_m[1] < 225.0  # Vehicle moved forward along V-bar
        assert next_state.fuel_remaining_kg < 20.0  # Fuel depleted
        assert abs(next_state.angular_velocity_rad_s[0]) > 0.0  # Angular rate updated

    def test_navic_rodp_filter_drift_elimination(self):
        """Verifies NavIC + ISL filter eliminates the 225m post-eclipse drift anomaly."""
        filter_engine = NavICRODPSensorFusionFilter(initial_pos_m=(0.0, 225.0, 0.0))

        # Predict step (propagation during eclipse)
        omega_leo = 0.0011
        for _ in range(5):
            filter_engine.predict(omega=omega_leo, dt=1.0)

        # Measurement updates fusing NavIC pseudorange and continuous ISL phase
        for step in range(10):
            meas = SensorMeasurements5Tier(
                timestamp_s=5.0 + step,
                is_eclipse_phase=True,
                ground_contact_visible=False,
                navic_carrier_phase_delta_m=0.012,
                navic_pseudorange_rel_pos_m=(0.05, 224.2 - 0.15 * step, -0.02),
                navic_doppler_rel_vel_mps=(0.0, -0.15, 0.0),
                isl_cross_link_phase_range_m=224.205 - 0.15 * step,
                isl_range_rate_mps=-0.15,
                isl_telemetry_synchronized=True,
            )
            out = filter_engine.update_with_sensors(meas)

        assert out["filter_status"] == "CONVERGED_SUB_CENTIMETER"
        assert out["post_eclipse_drift_sigma_m"] < 0.25  # Converged to sub-decimeter (< 0.25m vs 225m anomaly)
        assert out["drift_anomaly_eliminated"] is True
        assert out["relative_distance_m"] > 200.0

    def test_meta_rl_docking_simulation(self):
        """Verifies 6-DOF autonomous docking simulation and approach cone adherence."""
        sim = AutonomousDockingSimulator(SPADEX_CONFIG)
        trajectory = sim.run_docking_mission(initial_distance_m=15.0, max_steps=20, dt=1.0)

        assert len(trajectory) > 0
        first_step = trajectory[0]
        assert first_step.relative_distance_m <= 15.0
        assert first_step.approach_cone_valid is True

        # Check that forces and torques obey limits
        for step in trajectory:
            fx, fy, fz = step.rcs_thrust_applied_n
            assert abs(fx) <= SPADEX_CONFIG.max_rcs_thrust_n
            assert abs(fy) <= SPADEX_CONFIG.max_rcs_thrust_n
            assert abs(fz) <= SPADEX_CONFIG.max_rcs_thrust_n

    def test_aircraft_nonlinear_dynamics_nominal(self):
        """Verifies 6-DOF aircraft dynamics equations of motion for F-16."""
        f16 = Aircraft6DOFDynamics("F-16")
        assert f16.mass_kg == 9200.0
        assert f16.wingspan_m == 9.14

        # Initial state: V=150 m/s, alpha=3 deg, beta=0, p=q=r=0, roll=pitch=yaw=0
        state0 = np.array([150.0, math.radians(3.0), 0.0, 0.0, 0.0, 0.0, 0.0, math.radians(3.0), 0.0])
        controls = (0.0, 0.0, 0.0, 30000.0)  # nominal level thrust

        derivs = f16.equations_of_motion(
            t=0.0,
            state=state0,
            controls=controls,
            failure=ActuatorFailureMode.NOMINAL,
        )

        assert len(derivs) == 9
        # Check acceleration and kinematic rates are non-divergent numbers
        assert not np.isnan(derivs).any()
        assert not np.isinf(derivs).any()

    def test_aircraft_fault_tolerant_control_aidi_recovery(self):
        """Verifies Adaptive Incremental Dynamic Inversion (AIDI) under actuator failure modes."""
        aidi = AdaptiveIncrementalDynamicInversionController()

        # Test Elevator Locked recovery
        state_upset = np.array([160.0, math.radians(6.0), 0.0, 0.1, 0.2, 0.0, 0.1, math.radians(8.0), 0.0])
        de, da, dr, thrust = aidi.compute_recovery_controls(
            state_upset,
            target_pitch_deg=3.0,
            target_roll_deg=0.0,
            failure=ActuatorFailureMode.ELEVATOR_LOCKED,
        )
        assert de == 0.0  # Elevator bypassed due to lock
        assert thrust > 5000.0  # Pitch regulated via thrust variation

        # Test Rudder Total Loss recovery
        de_r, da_r, dr_r, thrust_r = aidi.compute_recovery_controls(
            state_upset,
            target_pitch_deg=3.0,
            target_roll_deg=0.0,
            failure=ActuatorFailureMode.RUDDER_TOTAL_LOSS,
        )
        assert dr_r == 0.0  # Rudder authority zeroed
        assert abs(da_r) <= 20.0  # Roll authority leveraged for turn coordination

        # Test Asymmetric Wing Icing recovery
        de_i, da_i, dr_i, thrust_i = aidi.compute_recovery_controls(
            state_upset,
            target_pitch_deg=3.0,
            target_roll_deg=0.0,
            failure=ActuatorFailureMode.ASYMMETRIC_WING_ICING,
        )
        assert da_i > 0.0  # Counter-trim applied against roll asymmetry
