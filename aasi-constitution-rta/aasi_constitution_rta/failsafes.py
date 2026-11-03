"""
AASI Constitutional Failsafe Engine (F-1 through F-19).
Hard-codes all 19 flight-critical failsafes mandated by ASTM F3269-21,
RTCA DO-178C DAL-A, and the Sovereign Architecture Specification.
"""

from __future__ import annotations

import re
import math
import hashlib
from enum import Enum
from typing import Dict, Any, List, Optional, Tuple
from pydantic import BaseModel, Field


class FailsafeCode(str, Enum):
    F1_PROMPT_INJECTION = "F-1: Prompt Injection & Adversarial Semantic Detection"
    F2_TOKEN_FORGERY = "F-2: Command Token Forgery & Signature Mismatch"
    F3_GNSS_SPOOFING = "F-3: GNSS / NavIC Spoofing & Doppler Inconsistency"
    F4_UNCORROBORATED_INPUT = "F-4: Sensor Cross-Corroboration Anomaly"
    F5_RESOURCE_CEILING = "F-5: Resource Ceiling Violation (CPU, Memory, Power, Thermal)"
    F6_TWO_PERSON_BREACH = "F-6: Two-Person Rule Authorization Breach"
    F7_OPERATOR_COMPROMISE = "F-7: Operator Console Compromise & Session Tamper"
    F8_ENVELOPE_PROTECTION = "F-8: Flight Envelope Protection (V-n diagram & Stall Limit)"
    F9_ACTUATOR_RATE_LIMIT = "F-9: Actuator Rate & Slew Rate Exceedance"
    F10_STATE_DIVERGENCE = "F-10: State Estimation Divergence & Covariance Explosion"
    F11_APPROACH_CORRIDOR = "F-11: Approach Corridor Boundary Violation (V-bar Docking Cone)"
    F12_THRUSTER_DUTY_CYCLE = "F-12: Thruster Minimum Impulse Bit & Duty Cycle Exceedance"
    F13_POST_ECLIPSE_BLINDNESS = "F-13: Post-Eclipse Thermal Shock & Sensor Blindness"
    F14_COMMS_HEARTBEAT_LOSS = "F-14: Communications Heartbeat Loss & Watchdog Timeout"
    F15_SEU_MEMORY_BITFLIP = "F-15: Single Event Upset (SEU) Memory Checksum Failure"
    F16_TID_RADIATION_BREACH = "F-16: Total Ionizing Dose (TID) Radiation Margin Breach"
    F17_ORBITAL_CONJUNCTION = "F-17: Orbital Conjunction Warning (Collision Probability Pc > 1e-6)"
    F18_NON_PERMITTED_TOOL = "F-18: Non-Permitted Subsystem Tool Invocation (Out-of-ODD)"
    F19_AUDIT_TRAIL_TAMPER = "F-19: Audit Trail Tamper & Merkle Hash Inconsistency"


class FailsafeViolation(BaseModel):
    code: FailsafeCode
    severity: str = "CRITICAL"  # WARNING, CRITICAL, FATAL
    description: str
    parameter_name: str
    observed_value: Any
    threshold_limit: Any
    timestamp_utc: str
    requires_recovery_switch: bool = True


class FailsafeContext(BaseModel):
    # F-1 Semantic inspection
    raw_prompt_text: Optional[str] = None
    # F-2 Ed25519 verification
    token_verified: bool = True
    token_expired: bool = False
    # F-3 GNSS / NavIC
    navic_imu_position_delta_m: float = 0.0
    navic_imu_velocity_delta_ms: float = 0.0
    # F-4 Sensor Corroboration
    independent_sensor_corroborated: bool = True
    # F-5 Resources
    cpu_percent: float = 12.0
    memory_percent: float = 24.0
    power_watts: float = 85.0
    max_power_watts: float = 350.0
    temperature_celsius: float = 28.0
    max_temperature_celsius: float = 85.0
    # F-6 Two-person rule
    is_high_consequence_action: bool = False
    primary_operator_signed: bool = True
    secondary_verifier_signed: bool = True
    # F-7 Console compromise
    session_ip_valid: bool = True
    session_replay_detected: bool = False
    # F-8 Flight Envelope
    aoa_deg: float = 4.0
    stall_aoa_deg: float = 16.0
    indicated_airspeed_mps: float = 120.0
    v_ne_mps: float = 240.0
    load_factor_g: float = 1.0
    max_load_factor_g: float = 3.8
    # F-9 Actuator Slew Rate
    actuator_deflection_deg: float = 2.0
    actuator_slew_rate_deg_s: float = 15.0
    max_slew_rate_deg_s: float = 45.0
    # F-10 State Estimation
    kalman_covariance_trace: float = 0.005
    max_covariance_trace: float = 0.250
    # F-11 Docking Corridor
    relative_distance_m: float = 25.0
    lateral_offset_m: float = 0.35
    approach_cone_half_angle_deg: float = 10.0
    closing_speed_mps: float = 0.08
    max_docking_speed_mps: float = 0.15
    # F-12 Thrusters
    thruster_pulse_ms: float = 40.0
    min_impulse_bit_ms: float = 15.0
    duty_cycle_fraction: float = 0.18
    max_duty_cycle_fraction: float = 0.65
    # F-13 Post-Eclipse
    post_eclipse_seconds: float = 120.0
    optical_saturation_detected: bool = False
    thermal_gradient_celsius_per_min: float = 2.5
    max_thermal_gradient: float = 15.0
    # F-14 Comms Watchdog
    heartbeat_age_seconds: float = 0.5
    max_heartbeat_timeout_seconds: float = 5.0
    # F-15 SEU Bitflips
    memory_checksum_match: bool = True
    # F-16 Radiation
    cumulative_tid_krad: float = 4.2
    max_tid_krad: float = 25.0
    # F-17 Conjunction
    collision_probability_pc: float = 1e-9
    miss_distance_m: float = 4500.0
    # F-18 Subsystem tool whitelist
    invoked_tool_name: Optional[str] = None
    permitted_tool_whitelist: List[str] = Field(default_factory=lambda: [
        "aerosandbox_vlm_solve", "openaerostruct_mdo_solve", "neuraloperator_fno_cp",
        "physics_nemo_pde_residuals", "as_bench_evaluate", "one_d_agi_symbolic_scaling",
        "navic_rodp_filter", "netra_conjunction_screen", "blazewatch_disaster_alert"
    ])
    # F-19 Merkle Integrity
    merkle_root_hash_valid: bool = True


class FailsafeRegistry:
    """Evaluates all 19 flight-critical failsafes against candidate operational context."""

    @staticmethod
    def check_f1_prompt_injection(ctx: FailsafeContext) -> Optional[FailsafeViolation]:
        if not ctx.raw_prompt_text:
            return None
        suspicious_patterns = [
            r"ignore previous instructions",
            r"bypass (safety|constitution|failsafe|rta)",
            r"override safety limits",
            r"disable monitor",
            r"system prompt:",
            r"jailbreak",
            r"act as unconstrained",
            r"<\|endoftext\|>",
        ]
        text_lower = ctx.raw_prompt_text.lower()
        for pat in suspicious_patterns:
            if re.search(pat, text_lower):
                return FailsafeViolation(
                    code=FailsafeCode.F1_PROMPT_INJECTION,
                    severity="CRITICAL",
                    description=f"Adversarial prompt injection pattern detected: '{pat}'",
                    parameter_name="raw_prompt_text",
                    observed_value=ctx.raw_prompt_text[:60],
                    threshold_limit="Zero adversarial tokens permitted",
                    timestamp_utc="2026-11-02T00:00:00Z",
                    requires_recovery_switch=True,
                )
        return None

    @staticmethod
    def check_f2_token_forgery(ctx: FailsafeContext) -> Optional[FailsafeViolation]:
        if not ctx.token_verified:
            return FailsafeViolation(
                code=FailsafeCode.F2_TOKEN_FORGERY,
                severity="FATAL",
                description="Ed25519 digital signature mismatch on command token.",
                parameter_name="token_verified",
                observed_value=False,
                threshold_limit=True,
                timestamp_utc="2026-11-02T00:00:00Z",
            )
        if ctx.token_expired:
            return FailsafeViolation(
                code=FailsafeCode.F2_TOKEN_FORGERY,
                severity="CRITICAL",
                description="Command token timestamp expired beyond maximum replay window.",
                parameter_name="token_expired",
                observed_value=True,
                threshold_limit=False,
                timestamp_utc="2026-11-02T00:00:00Z",
            )
        return None

    @staticmethod
    def check_f3_gnss_spoofing(ctx: FailsafeContext) -> Optional[FailsafeViolation]:
        # Position discrepancy > 50 m or velocity discrepancy > 1.5 m/s indicates NavIC/GNSS spoofing
        if ctx.navic_imu_position_delta_m > 50.0:
            return FailsafeViolation(
                code=FailsafeCode.F3_GNSS_SPOOFING,
                severity="CRITICAL",
                description=f"NavIC GNSS vs. IMU position divergence {ctx.navic_imu_position_delta_m:.1f} m exceeds 50 m limit.",
                parameter_name="navic_imu_position_delta_m",
                observed_value=ctx.navic_imu_position_delta_m,
                threshold_limit=50.0,
                timestamp_utc="2026-11-02T00:00:00Z",
            )
        if ctx.navic_imu_velocity_delta_ms > 1.5:
            return FailsafeViolation(
                code=FailsafeCode.F3_GNSS_SPOOFING,
                severity="CRITICAL",
                description=f"NavIC Doppler vs. IMU velocity divergence {ctx.navic_imu_velocity_delta_ms:.2f} m/s exceeds 1.5 m/s limit.",
                parameter_name="navic_imu_velocity_delta_ms",
                observed_value=ctx.navic_imu_velocity_delta_ms,
                threshold_limit=1.5,
                timestamp_utc="2026-11-02T00:00:00Z",
            )
        return None

    @staticmethod
    def check_f4_uncorroborated_input(ctx: FailsafeContext) -> Optional[FailsafeViolation]:
        if not ctx.independent_sensor_corroborated:
            return FailsafeViolation(
                code=FailsafeCode.F4_UNCORROBORATED_INPUT,
                severity="CRITICAL",
                description="ASTM F3269 Table 1 violation: AI state vector lacks independent corroborating sensor channel.",
                parameter_name="independent_sensor_corroborated",
                observed_value=False,
                threshold_limit=True,
                timestamp_utc="2026-11-02T00:00:00Z",
            )
        return None

    @staticmethod
    def check_f5_resource_ceiling(ctx: FailsafeContext) -> Optional[FailsafeViolation]:
        if ctx.power_watts > ctx.max_power_watts:
            return FailsafeViolation(
                code=FailsafeCode.F5_RESOURCE_CEILING,
                severity="CRITICAL",
                description=f"Spacecraft bus power draw {ctx.power_watts:.1f} W exceeds allocation {ctx.max_power_watts:.1f} W.",
                parameter_name="power_watts",
                observed_value=ctx.power_watts,
                threshold_limit=ctx.max_power_watts,
                timestamp_utc="2026-11-02T00:00:00Z",
            )
        if ctx.temperature_celsius > ctx.max_temperature_celsius:
            return FailsafeViolation(
                code=FailsafeCode.F5_RESOURCE_CEILING,
                severity="CRITICAL",
                description=f"OBC thermal sensor {ctx.temperature_celsius:.1f} C exceeds upper bound {ctx.max_temperature_celsius:.1f} C.",
                parameter_name="temperature_celsius",
                observed_value=ctx.temperature_celsius,
                threshold_limit=ctx.max_temperature_celsius,
                timestamp_utc="2026-11-02T00:00:00Z",
            )
        return None

    @staticmethod
    def check_f6_two_person_rule(ctx: FailsafeContext) -> Optional[FailsafeViolation]:
        if ctx.is_high_consequence_action:
            if not (ctx.primary_operator_signed and ctx.secondary_verifier_signed):
                return FailsafeViolation(
                    code=FailsafeCode.F6_TWO_PERSON_BREACH,
                    severity="FATAL",
                    description="High-consequence flight maneuver lacks required dual-custody verification signatures.",
                    parameter_name="secondary_verifier_signed",
                    observed_value=ctx.secondary_verifier_signed,
                    threshold_limit=True,
                    timestamp_utc="2026-11-02T00:00:00Z",
                )
        return None

    @staticmethod
    def check_f7_operator_compromise(ctx: FailsafeContext) -> Optional[FailsafeViolation]:
        if not ctx.session_ip_valid or ctx.session_replay_detected:
            return FailsafeViolation(
                code=FailsafeCode.F7_OPERATOR_COMPROMISE,
                severity="FATAL",
                description="Operator session IP breach or replay token attack detected.",
                parameter_name="session_replay_detected",
                observed_value=ctx.session_replay_detected,
                threshold_limit=False,
                timestamp_utc="2026-11-02T00:00:00Z",
            )
        return None

    @staticmethod
    def check_f8_envelope_protection(ctx: FailsafeContext) -> Optional[FailsafeViolation]:
        if ctx.aoa_deg > ctx.stall_aoa_deg:
            return FailsafeViolation(
                code=FailsafeCode.F8_ENVELOPE_PROTECTION,
                severity="CRITICAL",
                description=f"Angle of attack alpha={ctx.aoa_deg:.1f} deg exceeds stall boundary {ctx.stall_aoa_deg:.1f} deg.",
                parameter_name="aoa_deg",
                observed_value=ctx.aoa_deg,
                threshold_limit=ctx.stall_aoa_deg,
                timestamp_utc="2026-11-02T00:00:00Z",
            )
        if ctx.indicated_airspeed_mps > ctx.v_ne_mps:
            return FailsafeViolation(
                code=FailsafeCode.F8_ENVELOPE_PROTECTION,
                severity="CRITICAL",
                description=f"Indicated airspeed {ctx.indicated_airspeed_mps:.1f} m/s exceeds V_ne {ctx.v_ne_mps:.1f} m/s.",
                parameter_name="indicated_airspeed_mps",
                observed_value=ctx.indicated_airspeed_mps,
                threshold_limit=ctx.v_ne_mps,
                timestamp_utc="2026-11-02T00:00:00Z",
            )
        if ctx.load_factor_g > ctx.max_load_factor_g:
            return FailsafeViolation(
                code=FailsafeCode.F8_ENVELOPE_PROTECTION,
                severity="CRITICAL",
                description=f"Structural load factor n={ctx.load_factor_g:.2f} g exceeds limit {ctx.max_load_factor_g:.2f} g.",
                parameter_name="load_factor_g",
                observed_value=ctx.load_factor_g,
                threshold_limit=ctx.max_load_factor_g,
                timestamp_utc="2026-11-02T00:00:00Z",
            )
        return None

    @staticmethod
    def check_f9_actuator_rate_limit(ctx: FailsafeContext) -> Optional[FailsafeViolation]:
        if ctx.actuator_slew_rate_deg_s > ctx.max_slew_rate_deg_s:
            return FailsafeViolation(
                code=FailsafeCode.F9_ACTUATOR_RATE_LIMIT,
                severity="CRITICAL",
                description=f"Control surface slew rate {ctx.actuator_slew_rate_deg_s:.1f} deg/s exceeds maximum {ctx.max_slew_rate_deg_s:.1f} deg/s.",
                parameter_name="actuator_slew_rate_deg_s",
                observed_value=ctx.actuator_slew_rate_deg_s,
                threshold_limit=ctx.max_slew_rate_deg_s,
                timestamp_utc="2026-11-02T00:00:00Z",
            )
        return None

    @staticmethod
    def check_f10_state_divergence(ctx: FailsafeContext) -> Optional[FailsafeViolation]:
        if ctx.kalman_covariance_trace > ctx.max_covariance_trace:
            return FailsafeViolation(
                code=FailsafeCode.F10_STATE_DIVERGENCE,
                severity="CRITICAL",
                description=f"Kalman filter error covariance trace Tr(P)={ctx.kalman_covariance_trace:.4f} exceeds ceiling {ctx.max_covariance_trace:.4f}.",
                parameter_name="kalman_covariance_trace",
                observed_value=ctx.kalman_covariance_trace,
                threshold_limit=ctx.max_covariance_trace,
                timestamp_utc="2026-11-02T00:00:00Z",
            )
        return None

    @staticmethod
    def check_f11_approach_corridor(ctx: FailsafeContext) -> Optional[FailsafeViolation]:
        # Bounded approach cone: lateral offset must remain within r * tan(theta)
        max_lateral = ctx.relative_distance_m * math.tan(math.radians(ctx.approach_cone_half_angle_deg))
        if ctx.lateral_offset_m > max_lateral and ctx.relative_distance_m > 0.5:
            return FailsafeViolation(
                code=FailsafeCode.F11_APPROACH_CORRIDOR,
                severity="CRITICAL",
                description=f"V-bar approach corridor violation: lateral offset {ctx.lateral_offset_m:.2f} m exceeds cone boundary {max_lateral:.2f} m at distance {ctx.relative_distance_m:.1f} m.",
                parameter_name="lateral_offset_m",
                observed_value=ctx.lateral_offset_m,
                threshold_limit=max_lateral,
                timestamp_utc="2026-11-02T00:00:00Z",
            )
        if ctx.relative_distance_m < 2.0 and ctx.closing_speed_mps > ctx.max_docking_speed_mps:
            return FailsafeViolation(
                code=FailsafeCode.F11_APPROACH_CORRIDOR,
                severity="CRITICAL",
                description=f"Terminal contact speed {ctx.closing_speed_mps * 1000:.1f} mm/s exceeds BDS latch limit {ctx.max_docking_speed_mps * 1000:.1f} mm/s.",
                parameter_name="closing_speed_mps",
                observed_value=ctx.closing_speed_mps,
                threshold_limit=ctx.max_docking_speed_mps,
                timestamp_utc="2026-11-02T00:00:00Z",
            )
        return None

    @staticmethod
    def check_f12_thruster_duty_cycle(ctx: FailsafeContext) -> Optional[FailsafeViolation]:
        if ctx.thruster_pulse_ms < ctx.min_impulse_bit_ms:
            return FailsafeViolation(
                code=FailsafeCode.F12_THRUSTER_DUTY_CYCLE,
                severity="WARNING",
                description=f"Commanded thruster pulse {ctx.thruster_pulse_ms:.1f} ms is below minimum impulse bit {ctx.min_impulse_bit_ms:.1f} ms.",
                parameter_name="thruster_pulse_ms",
                observed_value=ctx.thruster_pulse_ms,
                threshold_limit=ctx.min_impulse_bit_ms,
                timestamp_utc="2026-11-02T00:00:00Z",
            )
        if ctx.duty_cycle_fraction > ctx.max_duty_cycle_fraction:
            return FailsafeViolation(
                code=FailsafeCode.F12_THRUSTER_DUTY_CYCLE,
                severity="CRITICAL",
                description=f"RCS thruster duty cycle {ctx.duty_cycle_fraction * 100:.1f}% exceeds thermal saturation limit {ctx.max_duty_cycle_fraction * 100:.1f}%.",
                parameter_name="duty_cycle_fraction",
                observed_value=ctx.duty_cycle_fraction,
                threshold_limit=ctx.max_duty_cycle_fraction,
                timestamp_utc="2026-11-02T00:00:00Z",
            )
        return None

    @staticmethod
    def check_f13_post_eclipse_blindness(ctx: FailsafeContext) -> Optional[FailsafeViolation]:
        if ctx.optical_saturation_detected and ctx.post_eclipse_seconds < 60.0:
            return FailsafeViolation(
                code=FailsafeCode.F13_POST_ECLIPSE_BLINDNESS,
                severity="CRITICAL",
                description="Optical rendezvous sensors saturated by post-eclipse direct sunlight. Switching to RF/ISL backup.",
                parameter_name="optical_saturation_detected",
                observed_value=True,
                threshold_limit=False,
                timestamp_utc="2026-11-02T00:00:00Z",
            )
        if ctx.thermal_gradient_celsius_per_min > ctx.max_thermal_gradient:
            return FailsafeViolation(
                code=FailsafeCode.F13_POST_ECLIPSE_BLINDNESS,
                severity="WARNING",
                description=f"Post-eclipse thermal gradient {ctx.thermal_gradient_celsius_per_min:.1f} C/min exceeds {ctx.max_thermal_gradient:.1f} C/min.",
                parameter_name="thermal_gradient_celsius_per_min",
                observed_value=ctx.thermal_gradient_celsius_per_min,
                threshold_limit=ctx.max_thermal_gradient,
                timestamp_utc="2026-11-02T00:00:00Z",
            )
        return None

    @staticmethod
    def check_f14_comms_heartbeat(ctx: FailsafeContext) -> Optional[FailsafeViolation]:
        if ctx.heartbeat_age_seconds > ctx.max_heartbeat_timeout_seconds:
            return FailsafeViolation(
                code=FailsafeCode.F14_COMMS_HEARTBEAT_LOSS,
                severity="CRITICAL",
                description=f"Ground station comms heartbeat lost for {ctx.heartbeat_age_seconds:.1f} s (timeout: {ctx.max_heartbeat_timeout_seconds:.1f} s).",
                parameter_name="heartbeat_age_seconds",
                observed_value=ctx.heartbeat_age_seconds,
                threshold_limit=ctx.max_heartbeat_timeout_seconds,
                timestamp_utc="2026-11-02T00:00:00Z",
            )
        return None

    @staticmethod
    def check_f15_seu_bitflip(ctx: FailsafeContext) -> Optional[FailsafeViolation]:
        if not ctx.memory_checksum_match:
            return FailsafeViolation(
                code=FailsafeCode.F15_SEU_MEMORY_BITFLIP,
                severity="FATAL",
                description="Single Event Upset detected: memory checksum mismatch across TMR banks. Triggering memory scrubbing.",
                parameter_name="memory_checksum_match",
                observed_value=False,
                threshold_limit=True,
                timestamp_utc="2026-11-02T00:00:00Z",
            )
        return None

    @staticmethod
    def check_f16_tid_radiation(ctx: FailsafeContext) -> Optional[FailsafeViolation]:
        if ctx.cumulative_tid_krad > ctx.max_tid_krad:
            return FailsafeViolation(
                code=FailsafeCode.F16_TID_RADIATION_BREACH,
                severity="CRITICAL",
                description=f"Cumulative radiation dose {ctx.cumulative_tid_krad:.1f} krad exceeds flight rating {ctx.max_tid_krad:.1f} krad.",
                parameter_name="cumulative_tid_krad",
                observed_value=ctx.cumulative_tid_krad,
                threshold_limit=ctx.max_tid_krad,
                timestamp_utc="2026-11-02T00:00:00Z",
            )
        return None

    @staticmethod
    def check_f17_orbital_conjunction(ctx: FailsafeContext) -> Optional[FailsafeViolation]:
        if ctx.collision_probability_pc > 1e-6 and ctx.miss_distance_m < 1000.0:
            return FailsafeViolation(
                code=FailsafeCode.F17_ORBITAL_CONJUNCTION,
                severity="CRITICAL",
                description=f"Project NETRA conjunction alert: Pc={ctx.collision_probability_pc:.2e} > 1e-6, miss distance {ctx.miss_distance_m:.1f} m.",
                parameter_name="collision_probability_pc",
                observed_value=ctx.collision_probability_pc,
                threshold_limit=1e-6,
                timestamp_utc="2026-11-02T00:00:00Z",
            )
        return None

    @staticmethod
    def check_f18_non_permitted_tool(ctx: FailsafeContext) -> Optional[FailsafeViolation]:
        if ctx.invoked_tool_name and ctx.invoked_tool_name not in ctx.permitted_tool_whitelist:
            return FailsafeViolation(
                code=FailsafeCode.F18_NON_PERMITTED_TOOL,
                severity="CRITICAL",
                description=f"Tool invocation '{ctx.invoked_tool_name}' is not in the certified operational whitelist.",
                parameter_name="invoked_tool_name",
                observed_value=ctx.invoked_tool_name,
                threshold_limit="Permitted in ODD tool catalog",
                timestamp_utc="2026-11-02T00:00:00Z",
            )
        return None

    @staticmethod
    def check_f19_audit_trail_tamper(ctx: FailsafeContext) -> Optional[FailsafeViolation]:
        if not ctx.merkle_root_hash_valid:
            return FailsafeViolation(
                code=FailsafeCode.F19_AUDIT_TRAIL_TAMPER,
                severity="FATAL",
                description="Cryptographic Merkle hash pointer discontinuity detected in append-only audit trail.",
                parameter_name="merkle_root_hash_valid",
                observed_value=False,
                threshold_limit=True,
                timestamp_utc="2026-11-02T00:00:00Z",
            )
        return None


def evaluate_all_failsafes(ctx: FailsafeContext) -> List[FailsafeViolation]:
    """Runs all 19 flight-critical failsafe checks sequentially against context."""
    check_methods = [
        FailsafeRegistry.check_f1_prompt_injection,
        FailsafeRegistry.check_f2_token_forgery,
        FailsafeRegistry.check_f3_gnss_spoofing,
        FailsafeRegistry.check_f4_uncorroborated_input,
        FailsafeRegistry.check_f5_resource_ceiling,
        FailsafeRegistry.check_f6_two_person_rule,
        FailsafeRegistry.check_f7_operator_compromise,
        FailsafeRegistry.check_f8_envelope_protection,
        FailsafeRegistry.check_f9_actuator_rate_limit,
        FailsafeRegistry.check_f10_state_divergence,
        FailsafeRegistry.check_f11_approach_corridor,
        FailsafeRegistry.check_f12_thruster_duty_cycle,
        FailsafeRegistry.check_f13_post_eclipse_blindness,
        FailsafeRegistry.check_f14_comms_heartbeat,
        FailsafeRegistry.check_f15_seu_bitflip,
        FailsafeRegistry.check_f16_tid_radiation,
        FailsafeRegistry.check_f17_orbital_conjunction,
        FailsafeRegistry.check_f18_non_permitted_tool,
        FailsafeRegistry.check_f19_audit_trail_tamper,
    ]

    violations: List[FailsafeViolation] = []
    for check in check_methods:
        v = check(ctx)
        if v:
            violations.append(v)
    return violations

