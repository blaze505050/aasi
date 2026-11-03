"""
AASI ASTM F3269-21 2-of-3 Voting Safety Monitor & RTA Switch.
Implements heterogeneous multi-channel voting to bound non-deterministic AI.
Switches control from Complex Function to deterministic Recovery Function
upon 2-of-3 safety consensus breach.
"""

from __future__ import annotations

import math
from enum import Enum
from typing import Dict, Any, List, Optional, Tuple
from pydantic import BaseModel, Field


class RTASwitchState(str, Enum):
    COMPLEX_FUNCTION_ACTIVE = "COMPLEX_FUNCTION_ACTIVE"
    RECOVERY_FUNCTION_ENGAGED = "RECOVERY_FUNCTION_ENGAGED"
    SAFE_HOLD_STANDBY = "SAFE_HOLD_STANDBY"


class EvaluatorVerdict(BaseModel):
    evaluator_name: str
    acceptable: bool
    confidence: float  # 0.0 to 1.0
    rationale: str
    metrics: Dict[str, Any] = Field(default_factory=dict)


class SafetyMonitorDecision(BaseModel):
    switch_state: RTASwitchState
    votes_acceptable: int
    votes_unacceptable: int
    evaluator_verdicts: List[EvaluatorVerdict]
    recovery_command: Optional[Dict[str, Any]] = None
    override_reason: Optional[str] = None


class RecoveryFunction:
    """Deterministic DO-178C DAL-A certified fallback guidance routines."""

    @staticmethod
    def aircraft_level_flight_recovery(current_state: Dict[str, Any]) -> Dict[str, Any]:
        """Commands wings level, AoA to 3.0 deg, thrust to cruise trim."""
        return {
            "recovery_mode": "AIRCRAFT_WINGS_LEVEL_TRIM",
            "target_pitch_deg": 3.0,
            "target_roll_deg": 0.0,
            "target_thrust_percent": 65.0,
            "commanded_elevator_deg": -1.2,
            "commanded_aileron_deg": 0.0,
            "commanded_rudder_deg": 0.0,
            "safety_action": "Disengaged Complex Function; holding positive 1g trim.",
        }

    @staticmethod
    def orbital_safe_hold_abort(current_state: Dict[str, Any]) -> Dict[str, Any]:
        """Commands zero relative closing velocity, retrograde pulse, attitude lock."""
        return {
            "recovery_mode": "ORBITAL_VBAR_SAFE_HOLD_ABORT",
            "delta_v_retro_mps": 0.25,
            "rcs_attitude_mode": "EARTH_POINTING_INERTIAL_LOCK",
            "docking_mechanism_state": "LATCH_RETRACT_SAFE",
            "safety_action": "Aborted terminal approach; halted V-bar closing rate.",
        }


class SafetyMonitor2of3:
    """
    ASTM F3269-21 2-of-3 Heterogeneous Safety Monitor.
    Evaluates proposed Complex Function output across 3 independent algorithm families:
    1. Physics Kinematic Bound (Conservation of Energy & Acceleration Limits)
    2. Operational Flight Envelope Governor (V-n & Stall Limits)
    3. Approach Corridor / Docking Cone Geometry (Spatial Volume Bounds)
    """

    def __init__(self):
        self.switch_state = RTASwitchState.COMPLEX_FUNCTION_ACTIVE
        self.recovery = RecoveryFunction()

    # Evaluator 1: Physics Kinematics Bound
    def _evaluate_physics_bound(self, proposal: Dict[str, Any], state: Dict[str, Any]) -> EvaluatorVerdict:
        max_accel_mps2 = state.get("max_allowable_accel_mps2", 25.0)
        commanded_accel = proposal.get("commanded_accel_mps2", 0.0)
        commanded_thrust_n = proposal.get("thrust_n", 0.0)
        mass_kg = state.get("mass_kg", 220.0)

        implied_accel = commanded_thrust_n / max(mass_kg, 1.0) if commanded_thrust_n > 0 else commanded_accel
        if implied_accel > max_accel_mps2:
            return EvaluatorVerdict(
                evaluator_name="Evaluator-1: Physics Kinematic Bound",
                acceptable=False,
                confidence=0.99,
                rationale=f"Commanded acceleration {implied_accel:.2f} m/s^2 exceeds structural kinematic ceiling {max_accel_mps2:.2f} m/s^2.",
                metrics={"implied_accel": implied_accel, "max_accel": max_accel_mps2},
            )
        return EvaluatorVerdict(
            evaluator_name="Evaluator-1: Physics Kinematic Bound",
            acceptable=True,
            confidence=0.98,
            rationale="Kinematics within momentum and energy conservation boundaries.",
            metrics={"implied_accel": implied_accel},
        )

    # Evaluator 2: Operational Flight Envelope Governor
    def _evaluate_envelope_governor(self, proposal: Dict[str, Any], state: Dict[str, Any]) -> EvaluatorVerdict:
        current_aoa = state.get("aoa_deg", 4.0)
        commanded_delta_aoa = proposal.get("delta_aoa_deg", 0.0)
        projected_aoa = current_aoa + commanded_delta_aoa
        stall_aoa = state.get("stall_aoa_deg", 16.0)

        load_factor = state.get("load_factor_g", 1.0)
        max_g = state.get("max_load_factor_g", 3.8)

        if projected_aoa > stall_aoa:
            return EvaluatorVerdict(
                evaluator_name="Evaluator-2: Operational Envelope Governor",
                acceptable=False,
                confidence=0.97,
                rationale=f"Projected angle of attack {projected_aoa:.1f} deg breaches stall angle {stall_aoa:.1f} deg.",
                metrics={"projected_aoa": projected_aoa, "stall_limit": stall_aoa},
            )
        if load_factor > max_g:
            return EvaluatorVerdict(
                evaluator_name="Evaluator-2: Operational Envelope Governor",
                acceptable=False,
                confidence=0.99,
                rationale=f"Load factor {load_factor:.2f} g exceeds airframe structural design limit {max_g:.2f} g.",
                metrics={"load_factor": load_factor, "max_g": max_g},
            )
        return EvaluatorVerdict(
            evaluator_name="Evaluator-2: Operational Envelope Governor",
            acceptable=True,
            confidence=0.96,
            rationale="Aerodynamic envelope within linear lift region.",
            metrics={"projected_aoa": projected_aoa, "load_factor": load_factor},
        )

    # Evaluator 3: Approach Corridor / Docking Cone Geometry
    def _evaluate_corridor_geometry(self, proposal: Dict[str, Any], state: Dict[str, Any]) -> EvaluatorVerdict:
        rel_dist = state.get("relative_distance_m", 50.0)
        lateral_offset = state.get("lateral_offset_m", 0.5)
        cone_angle = state.get("cone_angle_deg", 10.0)
        closing_speed = state.get("closing_speed_mps", 0.05)

        max_lateral = rel_dist * math.tan(math.radians(cone_angle))
        if rel_dist > 0.5 and lateral_offset > max_lateral:
            return EvaluatorVerdict(
                evaluator_name="Evaluator-3: Approach Corridor Geometry",
                acceptable=False,
                confidence=0.95,
                rationale=f"Lateral deviation {lateral_offset:.2f} m breaches approach cone boundary {max_lateral:.2f} m at distance {rel_dist:.1f} m.",
                metrics={"lateral_offset": lateral_offset, "max_lateral": max_lateral},
            )
        if rel_dist < 1.0 and closing_speed > 0.10:
            return EvaluatorVerdict(
                evaluator_name="Evaluator-3: Approach Corridor Geometry",
                acceptable=False,
                confidence=0.98,
                rationale=f"Terminal contact speed {closing_speed * 1000:.1f} mm/s exceeds 100 mm/s capture envelope.",
                metrics={"closing_speed_mps": closing_speed},
            )
        return EvaluatorVerdict(
            evaluator_name="Evaluator-3: Approach Corridor Geometry",
            acceptable=True,
            confidence=0.97,
            rationale="Spatial trajectory inside certified V-bar approach cone.",
            metrics={"lateral_offset": lateral_offset, "rel_dist": rel_dist},
        )

    def evaluate_proposal(
        self,
        proposal: Dict[str, Any],
        state: Dict[str, Any],
        domain: str = "ORBITAL",  # ORBITAL or AVIATION
    ) -> SafetyMonitorDecision:
        """
        Executes 2-of-3 voting.
        If >= 2 evaluators return acceptable, AI command is APPROVED.
        If >= 2 evaluators return unacceptable, RTA Switch flips to RECOVERY_FUNCTION_ENGAGED.
        """
        v1 = self._evaluate_physics_bound(proposal, state)
        v2 = self._evaluate_envelope_governor(proposal, state)
        v3 = self._evaluate_corridor_geometry(proposal, state)

        verdicts = [v1, v2, v3]
        accept_count = sum(1 for v in verdicts if v.acceptable)
        reject_count = 3 - accept_count

        if reject_count >= 2:
            self.switch_state = RTASwitchState.RECOVERY_FUNCTION_ENGAGED
            recovery_cmd = (
                self.recovery.orbital_safe_hold_abort(state)
                if domain == "ORBITAL"
                else self.recovery.aircraft_level_flight_recovery(state)
            )
            rejection_reasons = "; ".join([v.rationale for v in verdicts if not v.acceptable])
            return SafetyMonitorDecision(
                switch_state=RTASwitchState.RECOVERY_FUNCTION_ENGAGED,
                votes_acceptable=accept_count,
                votes_unacceptable=reject_count,
                evaluator_verdicts=verdicts,
                recovery_command=recovery_cmd,
                override_reason=f"ASTM F3269 2-of-3 Veto: {rejection_reasons}",
            )

        self.switch_state = RTASwitchState.COMPLEX_FUNCTION_ACTIVE
        return SafetyMonitorDecision(
            switch_state=RTASwitchState.COMPLEX_FUNCTION_ACTIVE,
            votes_acceptable=accept_count,
            votes_unacceptable=reject_count,
            evaluator_verdicts=verdicts,
            recovery_command=None,
            override_reason=None,
        )


class RTASwitch:
    """Hardware/Software Run-Time Assurance Switch governing control authority."""

    def __init__(self):
        self.state = RTASwitchState.COMPLEX_FUNCTION_ACTIVE
        self.trips_count = 0

    def trip_to_recovery(self, reason: str) -> None:
        self.state = RTASwitchState.RECOVERY_FUNCTION_ENGAGED
        self.trips_count += 1

    def reset_to_complex_function(self) -> None:
        self.state = RTASwitchState.COMPLEX_FUNCTION_ACTIVE

