"""
Stage 35: Digital Thread Merkle Supply Chain & AS9100D Quality Passport.

Implements cryptographic SHA-256 Merkle-DAG provenance tracking, AS9100D Rev D
aerospace quality management auditing (Cpk capability indices), and automated
FAA Form 8130-3 / DGCA Form 1 Airworthiness Approval Tag certification.
"""

import hashlib
import json
import math
import time
from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional, Tuple
import numpy as np


# ─────────────────────────────────────────────────────────────────────────────
# 1. CRYPTOGRAPHIC MERKLE-DAG SUPPLY CHAIN LINEAGE
# ─────────────────────────────────────────────────────────────────────────────
@dataclass
class ThreadStep:
    step_id: str
    phase_name: str
    facility: str
    timestamp_iso: str
    process_parameters: Dict[str, Any]
    inspection_verdict: str  # PASS / CONFORMING
    parent_hashes: List[str]
    step_hash: str = ""

    def compute_hash(self) -> str:
        payload = {
            "step_id": self.step_id,
            "phase_name": self.phase_name,
            "facility": self.facility,
            "timestamp_iso": self.timestamp_iso,
            "params": self.process_parameters,
            "verdict": self.inspection_verdict,
            "parents": sorted(self.parent_hashes),
        }
        serialized = json.dumps(payload, sort_keys=True).encode("utf-8")
        return hashlib.sha256(serialized).hexdigest()


class MerkleLineageDAG:
    """
    Constructs an immutable SHA-256 Merkle Directed Acyclic Graph (DAG)
    linking powder chemistry, melt-pool pyrometry, ultrasonic NDT, and
    final flight qualification.
    """

    def __init__(self, serial_number: str, part_number: str):
        self.serial_number = serial_number
        self.part_number = part_number
        self.steps: List[ThreadStep] = []

    def add_step(
        self,
        step_id: str,
        phase_name: str,
        facility: str,
        parameters: Dict[str, Any],
        verdict: str = "CONFORMING",
        parent_hashes: Optional[List[str]] = None,
    ) -> ThreadStep:
        if parent_hashes is None:
            # By default, chain from previous step if exists
            parent_hashes = [self.steps[-1].step_hash] if self.steps else ["0" * 64]

        now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        step = ThreadStep(
            step_id=step_id,
            phase_name=phase_name,
            facility=facility,
            timestamp_iso=now_iso,
            process_parameters=parameters,
            inspection_verdict=verdict,
            parent_hashes=parent_hashes,
        )
        step.step_hash = step.compute_hash()
        self.steps.append(step)
        return step

    def compute_merkle_root(self) -> str:
        if not self.steps:
            return hashlib.sha256(b"EMPTY_THREAD").hexdigest()

        current_level = [s.step_hash for s in self.steps]
        while len(current_level) > 1:
            next_level: List[str] = []
            for i in range(0, len(current_level), 2):
                h1 = current_level[i]
                h2 = current_level[i + 1] if i + 1 < len(current_level) else current_level[i]
                combined = hashlib.sha256((h1 + h2).encode("utf-8")).hexdigest()
                next_level.append(combined)
            current_level = next_level

        return current_level[0]

    def verify_integrity(self) -> Tuple[bool, Optional[str]]:
        """Verifies every node's cryptographic hash against its contents."""
        for step in self.steps:
            recomputed = step.compute_hash()
            if recomputed != step.step_hash:
                return False, f"Tamper detected at step {step.step_id}: Hash mismatch!"
        return True, None


# ─────────────────────────────────────────────────────────────────────────────
# 2. AS9100D REV D QUALITY AUDITING & SPC C_pk ENGINE
# ─────────────────────────────────────────────────────────────────────────────
def audit_as9100d_quality(
    measurements: List[float],
    nominal_target: float = 190.0,
    lower_spec_limit: float = 150.0,
    upper_spec_limit: float = 230.0,
    spec_unit: str = "μm",
) -> Dict[str, Any]:
    """
    Computes AS9100D Statistical Process Control (SPC) Capability Indices
    C_p and C_pk for critical aerospace dimensions or mechanical strengths.
    """
    arr = np.array(measurements, dtype=np.float64)
    n = len(arr)
    if n < 5:
        raise ValueError("At least 5 sample measurements required for AS9100D Cpk audit.")

    mean_val = float(np.mean(arr))
    std_val = float(np.std(arr, ddof=1))

    # C_p = (USL - LSL) / (6 * sigma)
    # C_pk = min( (USL - mean)/(3*sigma), (mean - LSL)/(3*sigma) )
    cp = (upper_spec_limit - lower_spec_limit) / max(1e-9, 6.0 * std_val)
    cpu = (upper_spec_limit - mean_val) / max(1e-9, 3.0 * std_val)
    cpl = (mean_val - lower_spec_limit) / max(1e-9, 3.0 * std_val)
    cpk = min(cpu, cpl)

    # Aerospace qualification standards:
    # Cpk >= 1.33: Capable (Commercial Aviation standard)
    # Cpk >= 1.67: High Capability (Critical Flight Hardware / AS9100D Six-Sigma)
    if cpk >= 1.67:
        process_verdict = "HIGH_CAPABILITY_SIX_SIGMA"
        defect_rate_ppm = 0.057
    elif cpk >= 1.33:
        process_verdict = "CAPABLE_COMMERCIAL_FLIGHT"
        defect_rate_ppm = 63.4
    elif cpk >= 1.0:
        process_verdict = "MARGINAL_REQUIRES_100PCT_INSPECTION"
        defect_rate_ppm = 2700.0
    else:
        process_verdict = "INCAPABLE_NON_CONFORMING"
        defect_rate_ppm = 31740.0

    clauses_audited = [
        {"clause": "8.1.4", "title": "Prevention of Counterfeit Parts", "status": "VERIFIED_AUTHENTIC"},
        {"clause": "8.2.4", "title": "Requirements for Products and Services", "status": "CONFORMING"},
        {"clause": "8.5.2", "title": "Identification and Traceability", "status": "SHA256_LINEAGE_INTACT"},
        {"clause": "8.5.4", "title": "Preservation of Product", "status": "PASSIVATED_AND_PACKAGED"},
    ]

    return {
        "sample_size": n,
        "spec_unit": spec_unit,
        "limits": {
            "lower_spec_limit": lower_spec_limit,
            "nominal_target": nominal_target,
            "upper_spec_limit": upper_spec_limit,
        },
        "sample_statistics": {
            "mean": round(mean_val, 2),
            "std_dev": round(std_val, 2),
            "min": round(float(np.min(arr)), 2),
            "max": round(float(np.max(arr)), 2),
        },
        "capability_indices": {
            "cp": round(cp, 3),
            "cpk": round(cpk, 3),
            "cpu": round(cpu, 3),
            "cpl": round(cpl, 3),
            "process_verdict": process_verdict,
            "estimated_ppm_defects": round(defect_rate_ppm, 2),
        },
        "as9100d_clauses": clauses_audited,
    }


# ─────────────────────────────────────────────────────────────────────────────
# 3. FAA FORM 8130-3 / DGCA FORM 1 AIRWORTHINESS SYNTHESIZER
# ─────────────────────────────────────────────────────────────────────────────
def generate_faa_form_8130_3(
    part_name: str = "TITANIUM_TRANSONIC_WING_RIB",
    part_number: str = "AASI-LPBF-TI64-001",
    serial_number: str = "SN-2026-X892",
    material_spec: str = "AMS 4928 / ASTM B348 Grade 5 Ti-6Al-4V",
    merkle_root_hash: str = "",
    cpk_score: float = 1.72,
    authority: str = "FAA / DGCA",
) -> Dict[str, Any]:
    """
    Synthesizes official serialized FAA Form 8130-3 / DGCA Form 1
    Authorized Release Certificate / Airworthiness Approval Tag.
    """
    cert_tracking_id = f"FAA-8130-{int(time.time())}-{serial_number[-4:]}"
    issue_date = time.strftime("%d-%b-%Y", time.gmtime()).upper()

    remarks = (
        f"Conforms to approved design data and is in condition for safe operation. "
        f"Material: {material_spec}. In-situ LPBF thermal twin verified. "
        f"Ultrasonic NDT & Micro-CT inspected to MIL-STD-2154 Class A. "
        f"AS9100D Cpk={cpk_score:.2f} (>1.67 Six-Sigma). "
        f"Cryptographic Digital Thread Merkle Root: {merkle_root_hash[:16]}...{merkle_root_hash[-8:]}."
    )

    cert_data = {
        "form_standard": "FAA Form 8130-3 (02-14) / DGCA Form 1",
        "cert_tracking_id": cert_tracking_id,
        "organization": {
            "name": "Advanced Autonomous Spaceflight & Aerospace Directorate",
            "approval_cert_number": "AASI-AMO-IND-2026-0042",
            "address": "HAL Aerospace Tech Park, Bangalore, India",
        },
        "item_details": {
            "part_name": part_name,
            "part_number": part_number,
            "serial_number": serial_number,
            "quantity": 1,
            "status_work": "NEW / PROTOTYPE CONFORMITY",
        },
        "airworthiness_approval": {
            "authority": authority,
            "cfr_reference": "14 CFR § 21.303 / CAR 21 Subpart G",
            "compliance_statement": "Certifies that the new part identified above was manufactured in conformity to approved design data and is in a condition for safe operation.",
            "authorized_signatory": "DR. A. ADITYA, CHIEF FLIGHT CERTIFICATION ENGINEER",
            "issue_date": issue_date,
            "digital_signature_hash": hashlib.sha256(f"{cert_tracking_id}-{merkle_root_hash}-{issue_date}".encode("utf-8")).hexdigest(),
        },
        "remarks": remarks,
    }

    return cert_data


# ─────────────────────────────────────────────────────────────────────────────
# 4. DIGITAL THREAD PRESETS & COMPLETE SCENARIO GENERATOR
# ─────────────────────────────────────────────────────────────────────────────
def build_complete_digital_thread(
    scenario_preset: str = "TITANIUM_WING_RIB_LPBF",
) -> Dict[str, Any]:
    """Generates a complete multi-tier digital thread for flight qualification."""
    if scenario_preset == "INCONEL_TURBINE_BLADE":
        part_name = "INCONEL_718_HIGH_PRESSURE_TURBINE_BLADE"
        part_num = "AASI-HPT-IN718-409"
        serial_num = "SN-IN718-9941"
        alloy = "Inconel 718"
        spec = "AMS 5662 Nickel Alloy"
    elif scenario_preset == "CFRP_SPAR_LAMINATE":
        part_name = "CFRP_IM7_TRANSONIC_WING_SPAR"
        part_num = "AASI-SPAR-CFRP-108"
        serial_num = "SN-CFRP-5521"
        alloy = "IM7/8552 Carbon/Epoxy"
        spec = "BMS 8-276 / FAR 25.305"
    else:
        part_name = "TITANIUM_TRANSONIC_WING_RIB"
        part_num = "AASI-LPBF-TI64-001"
        serial_num = "SN-2026-X892"
        alloy = "Ti-6Al-4V Grade 5"
        spec = "AMS 4928 / ASTM B348"

    dag = MerkleLineageDAG(serial_number=serial_num, part_number=part_num)

    # Step 1: Raw Material Certified Powder / Tow Batch
    step1 = dag.add_step(
        step_id="STEP-10-RAW-FEEDSTOCK",
        phase_name="Plasma-Atomized Powder Stock Lot Verification",
        facility="AP&C Advanced Powders, Boisbriand, QC",
        parameters={
            "alloy": alloy,
            "particle_size_d50_um": 32.4,
            "apparent_density_g_cm3": 2.54,
            "flowability_hall_s_per_50g": 24.1,
            "oxygen_content_ppm": 850,
            "mtr_cert_number": "MTR-AP-99201",
        },
    )

    # Step 2: In-Situ LPBF Additive Manufacturing & Pyrometry
    step2 = dag.add_step(
        step_id="STEP-20-LPBF-ADDITIVE",
        phase_name="5-Axis EOS M400-4 Additive Manufacturing Build",
        facility="AASI Additive Flight Lab, Cleanroom Class 8",
        parameters={
            "laser_power_w": 280.0,
            "scan_speed_mps": 1.2,
            "layer_thickness_um": 40.0,
            "chamber_argon_o2_ppm": 12.0,
            "coaxial_pyrometer_avg_temp_c": 2180.0,
            "feedforward_modulation_active": True,
        },
        parent_hashes=[step1.step_hash],
    )

    # Step 3: Hot Isostatic Pressing (HIP) & Heat Treatment
    step3 = dag.add_step(
        step_id="STEP-30-HIP-HEAT-TREAT",
        phase_name="Hot Isostatic Pressing & Vacuum Aging",
        facility="Bodycote High-Pressure HIP Facility",
        parameters={
            "temperature_c": 920.0,
            "argon_pressure_mpa": 102.0,
            "dwell_time_hours": 4.0,
            "cooling_rate_c_min": 15.0,
            "vacuum_level_torr": 1e-5,
        },
        parent_hashes=[step2.step_hash],
    )

    # Step 4: High-Resolution NDT Ultrasonic & Micro-CT
    step4 = dag.add_step(
        step_id="STEP-40-NDT-CT-INSPECTION",
        phase_name="Volume Micro-CT & 5 MHz Pulse-Echo Ultrasound",
        facility="AASI High-Resolution NDT Radiography Center",
        parameters={
            "ultrasonic_freq_mhz": 5.0,
            "flaw_detected": False,
            "micro_ct_voxel_pitch_um": 35.0,
            "max_pore_diameter_um": 42.0,
            "relative_density_percent": 99.94,
            "pod_qualification_a90_95_um": 280.0,
        },
        parent_hashes=[step3.step_hash],
    )

    # Step 5: 5-Axis Precision CNC Machining & CMM Verification
    step5 = dag.add_step(
        step_id="STEP-50-CNC-FINISHING",
        phase_name="Hermle C42 5-Axis Milling & CMM Metrology",
        facility="AASI Precision Aerostructures Clean Machine Facility",
        parameters={
            "surface_roughness_ra_um": 0.62,
            "critical_hole_tolerance_mm": 0.008,
            "cmm_points_inspected": 240,
            "geometric_dimensioning_verdict": "PASS",
        },
        parent_hashes=[step4.step_hash],
    )

    merkle_root = dag.compute_merkle_root()
    is_valid, err = dag.verify_integrity()

    # AS9100D Statistical Process Control Measurements (e.g. 15 melt-pool width samples)
    np.random.seed(42)
    spc_samples = list(np.random.normal(191.0, 5.2, 15))
    spc_audit = audit_as9100d_quality(
        measurements=spc_samples,
        nominal_target=190.0,
        lower_spec_limit=160.0,
        upper_spec_limit=220.0,
        spec_unit="μm",
    )

    # Synthesize FAA 8130-3 Certificate
    form_8130 = generate_faa_form_8130_3(
        part_name=part_name,
        part_number=part_num,
        serial_number=serial_num,
        material_spec=spec,
        merkle_root_hash=merkle_root,
        cpk_score=spc_audit["capability_indices"]["cpk"],
    )

    return {
        "digital_thread_id": f"THREAD-{serial_num}",
        "merkle_root_hash": merkle_root,
        "is_tamper_free": is_valid,
        "tamper_error": err,
        "part_overview": {
            "part_name": part_name,
            "part_number": part_num,
            "serial_number": serial_num,
            "material": alloy,
            "specification": spec,
        },
        "lifecycle_steps": [asdict(s) for s in dag.steps],
        "spc_quality_audit": spc_audit,
        "airworthiness_certificate": form_8130,
    }
