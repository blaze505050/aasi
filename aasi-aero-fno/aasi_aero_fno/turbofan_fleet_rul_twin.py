"""
Stage 40: Commercial Fleet Predictive Maintenance & Turbofan Remaining Useful Life (RUL) Digital Twin
======================================================================================================
Epoch VIII Capstone: High-bypass turbofan degradation physics, Paris-Erdogan low-cycle fatigue (LCF),
and Weibull hazard survival modeling conforming to:
- NASA C-MAPSS Commercial Modular Aero-Propulsion System Simulation degradation physics
- Exhaust Gas Temperature (EGT) margin erosion and compressor/turbine isentropic efficiency creep
- Paris-Erdogan law for high-pressure turbine (HPT) disk crack propagation:
  da/dN = C * (Delta_K)^m = C * (Y * Delta_sigma * sqrt(pi * a))^m
  with Inconel 718 / CMSX-4 superalloy fracture toughness K_Ic = 95.0 MPa*sqrt(m)
- Two-parameter Weibull reliability & hazard rate survival distribution:
  R(t) = exp(-(t/eta)^beta),  h(t) = (beta/eta) * (t/eta)^(beta - 1)
- Airline commercial economics: Unscheduled shop visit and Aircraft on Ground (AOG) cost prevention ($180k - $450k/engine)
"""

import math
import hashlib
import json
import time
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum


class TurbofanEngineModel(str, Enum):
    CFM_LEAP_1A = "CFM_LEAP_1A"       # Narrowbody A320neo / B737 MAX class, BPR 11:1
    GE90_115B = "GE90_115B"           # Widebody B777 class, BPR 9:1, 512 kN thrust
    KAVERI_GTX_35VS = "KAVERI_GTX_35VS" # Indigenous Afterburning Defense Turbofan


@dataclass
class TurbofanSpecifications:
    model: TurbofanEngineModel
    designation: str
    rated_thrust_kn: float
    bypass_ratio: float
    overall_pressure_ratio: float
    nominal_egt_celsius: float
    fresh_egt_margin_celsius: float
    critical_crack_length_mm: float
    paris_c: float
    paris_m: float
    stress_amplitude_mpa: float
    weibull_beta: float
    weibull_eta_cycles: float
    shop_visit_cost_usd: float


TURBOFAN_SPECS: Dict[TurbofanEngineModel, TurbofanSpecifications] = {
    TurbofanEngineModel.CFM_LEAP_1A: TurbofanSpecifications(
        model=TurbofanEngineModel.CFM_LEAP_1A,
        designation="CFM LEAP-1A26 (Narrowbody Commercial)",
        rated_thrust_kn=143.0,
        bypass_ratio=11.0,
        overall_pressure_ratio=40.0,
        nominal_egt_celsius=850.0,
        fresh_egt_margin_celsius=85.0,
        critical_crack_length_mm=12.5,
        paris_c=2.50e-12,
        paris_m=3.20,
        stress_amplitude_mpa=480.0,
        weibull_beta=2.85,
        weibull_eta_cycles=14000.0,
        shop_visit_cost_usd=280000.0,
    ),
    TurbofanEngineModel.GE90_115B: TurbofanSpecifications(
        model=TurbofanEngineModel.GE90_115B,
        designation="GE90-115B (Widebody Intercontinental)",
        rated_thrust_kn=512.0,
        bypass_ratio=9.0,
        overall_pressure_ratio=42.0,
        nominal_egt_celsius=920.0,
        fresh_egt_margin_celsius=90.0,
        critical_crack_length_mm=14.0,
        paris_c=2.20e-12,
        paris_m=3.15,
        stress_amplitude_mpa=510.0,
        weibull_beta=3.10,
        weibull_eta_cycles=16000.0,
        shop_visit_cost_usd=450000.0,
    ),
    TurbofanEngineModel.KAVERI_GTX_35VS: TurbofanSpecifications(
        model=TurbofanEngineModel.KAVERI_GTX_35VS,
        designation="GTX-35VS Kaveri (Defense Afterburning Fighter)",
        rated_thrust_kn=81.0,
        bypass_ratio=0.16,
        overall_pressure_ratio=21.5,
        nominal_egt_celsius=1050.0,
        fresh_egt_margin_celsius=65.0,
        critical_crack_length_mm=9.5,
        paris_c=3.00e-12,
        paris_m=3.25,
        stress_amplitude_mpa=580.0,
        weibull_beta=2.60,
        weibull_eta_cycles=8000.0,
        shop_visit_cost_usd=195000.0,
    ),
}


@dataclass
class TurbofanHealthDiagnosis:
    engine_model: str
    designation: str
    engine_serial_number: str
    flight_cycles_completed: int
    egt_margin_celsius: float
    egt_degradation_pct: float
    hpc_efficiency_loss_pct: float
    hpt_efficiency_loss_pct: float
    disk_crack_length_mm: float
    critical_crack_length_mm: float
    crack_growth_rate_mm_per_cycle: float
    stress_intensity_range_mpa_sqrt_m: float
    weibull_reliability_rt: float
    hazard_rate_per_cycle: float
    rul_cycles_remaining: int
    maintenance_status: str
    maintenance_action_recommended: str
    avoided_aog_savings_usd: float
    cryptographic_diagnosis_digest: str
    timestamp: str


class TurbofanFleetRulEngine:
    """
    Sovereign Turbofan Health & Predictive Maintenance Digital Twin Engine.
    Executes first-principles crack growth propagation, EGT margin tracking,
    and Weibull Remaining Useful Life (RUL) estimation.
    """

    GEOMETRY_FACTOR_Y = 1.12  # Standard edge crack stress concentration factor

    def evaluate_paris_crack_growth(
        self,
        specs: TurbofanSpecifications,
        cycles: int,
        initial_crack_mm: float = 0.5,
    ) -> Tuple[float, float, float]:
        """
        Integrates Paris' Law: da/dN = C * (Delta_K)^m = C * (Y * Delta_sigma * sqrt(pi * a))^m.
        Returns (current_crack_mm, current_growth_rate_mm_cycle, delta_k).
        """
        a_current = initial_crack_mm
        delta_sigma = specs.stress_amplitude_mpa
        c = specs.paris_c
        m = specs.paris_m
        y = self.GEOMETRY_FACTOR_Y

        # Adaptive integration over cycles
        step_cycles = max(1, cycles // 100) if cycles > 0 else 1
        n = 0

        while n < cycles:
            dn = min(step_cycles, cycles - n)
            # Crack in meters for stress intensity calculation
            a_m = max(1e-4, a_current * 1e-3)
            # Delta_K = Y * Delta_sigma * sqrt(pi * a) [MPa * sqrt(m)]
            delta_k = y * delta_sigma * math.sqrt(math.pi * a_m)
            # da/dN in meters per cycle
            da_dn_m = c * math.pow(delta_k, m)
            da_dn_mm = da_dn_m * 1000.0

            a_current += da_dn_mm * dn
            n += dn

            # Cap at critical crack length + 20%
            if a_current >= specs.critical_crack_length_mm * 1.2:
                a_current = specs.critical_crack_length_mm * 1.2
                break

        # Compute instantaneous values at final cycle
        a_m_final = max(1e-4, a_current * 1e-3)
        delta_k_final = y * delta_sigma * math.sqrt(math.pi * a_m_final)
        da_dn_final_mm = c * math.pow(delta_k_final, m) * 1000.0

        return a_current, da_dn_final_mm, delta_k_final

    def evaluate_egt_and_efficiencies(
        self,
        specs: TurbofanSpecifications,
        cycles: int,
    ) -> Tuple[float, float, float, float]:
        """
        Models NASA C-MAPSS EGT margin erosion and HPC/HPT isentropic efficiency degradation.
        Returns (egt_margin_celsius, egt_degradation_pct, hpc_loss_pct, hpt_loss_pct).
        """
        # Baseline erosion: ~0.005°C per cycle initially, accelerating past 80% life
        cycle_ratio = cycles / specs.weibull_eta_cycles
        erosion_celsius = specs.fresh_egt_margin_celsius * (0.85 * cycle_ratio + 0.35 * (cycle_ratio ** 2))
        current_egt_margin = max(0.0, specs.fresh_egt_margin_celsius - erosion_celsius)
        degradation_pct = min(100.0, (erosion_celsius / specs.fresh_egt_margin_celsius) * 100.0)

        # Compressor and turbine efficiency loss
        hpc_loss_pct = min(4.5, 0.4 + 3.8 * cycle_ratio)
        hpt_loss_pct = min(5.2, 0.5 + 4.2 * (cycle_ratio ** 1.2))

        return current_egt_margin, degradation_pct, hpc_loss_pct, hpt_loss_pct

    def evaluate_weibull_survival(
        self,
        specs: TurbofanSpecifications,
        cycles: int,
    ) -> Tuple[float, float, int]:
        """
        Computes Weibull reliability R(t), hazard rate h(t), and Remaining Useful Life (RUL).
        R(t) = exp(-(t/eta)^beta)
        h(t) = (beta/eta) * (t/eta)^(beta - 1)
        """
        t = max(0.0, float(cycles))
        beta = specs.weibull_beta
        eta = specs.weibull_eta_cycles

        # Reliability R(t)
        z = (t / eta) ** beta
        r_t = math.exp(-min(50.0, z))

        # Hazard rate h(t)
        h_t = (beta / eta) * ((t / eta) ** (beta - 1.0)) if t > 0 else 0.0

        # RUL: Estimated cycles remaining until R(t) drops to 0.10 (90% unreliability cutoff)
        # 0.10 = exp(-(t_fail/eta)^beta) -> t_fail = eta * (-ln(0.10))^(1/beta) = eta * (2.302585)^(1/beta)
        t_fail = eta * math.pow(2.302585, 1.0 / beta)
        rul_cycles = max(0, int(t_fail - t))

        return r_t, h_t, rul_cycles

    def diagnose_engine(
        self,
        engine_model: TurbofanEngineModel = TurbofanEngineModel.CFM_LEAP_1A,
        flight_cycles: int = 6800,
        serial_number: str = "ESN-LEAP-98421",
    ) -> TurbofanHealthDiagnosis:
        """
        Integrates all degradation models into an authoritative diagnosis and maintenance action plan.
        """
        specs = TURBOFAN_SPECS.get(engine_model, TURBOFAN_SPECS[TurbofanEngineModel.CFM_LEAP_1A])

        # 1. Crack growth propagation
        crack_mm, da_dn, delta_k = self.evaluate_paris_crack_growth(specs, flight_cycles)

        # 2. EGT & component efficiencies
        egt_margin, egt_deg_pct, hpc_loss, hpt_loss = self.evaluate_egt_and_efficiencies(specs, flight_cycles)

        # 3. Weibull reliability and RUL
        r_t, h_t, rul_cycles = self.evaluate_weibull_survival(specs, flight_cycles)

        # 4. Determine Maintenance Status & Action
        crack_ratio = crack_mm / specs.critical_crack_length_mm

        if crack_ratio >= 0.85 or egt_margin <= 5.0 or r_t < 0.20:
            status = "CRITICAL_AOG_RISK"
            action = "MANDATORY_SHOP_VISIT_AOG_PREVENTION: Immediate engine removal required; HPT disk inspection & borescope overhaul."
            avoided_cost = specs.shop_visit_cost_usd * 1.5
        elif crack_ratio >= 0.60 or egt_margin <= 20.0 or r_t < 0.50:
            status = "EXPEDITE_C_CHECK"
            action = "EXPEDITE_C_CHECK: Heavy base maintenance inspection recommended within next 250 flight cycles."
            avoided_cost = specs.shop_visit_cost_usd * 0.8
        elif crack_ratio >= 0.35 or egt_margin <= 40.0 or r_t < 0.80:
            status = "SCHEDULE_A_CHECK"
            action = "SCHEDULE_A_CHECK: Routine line maintenance borescope and compressor water-wash recommended."
            avoided_cost = specs.shop_visit_cost_usd * 0.3
        else:
            status = "NOMINAL_FLIGHT_SERVICE"
            action = "NOMINAL_FLIGHT_SERVICE: Airframe and powerplant operating within pristine green operating envelope."
            avoided_cost = 0.0

        # Cryptographic Digest
        timestamp_str = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        raw_diag = f"{serial_number}:{engine_model.value}:{flight_cycles}:{crack_mm:.3f}:{egt_margin:.2f}:{rul_cycles}:{timestamp_str}"
        digest_sha256 = hashlib.sha256(raw_diag.encode()).hexdigest()

        return TurbofanHealthDiagnosis(
            engine_model=engine_model.value,
            designation=specs.designation,
            engine_serial_number=serial_number,
            flight_cycles_completed=flight_cycles,
            egt_margin_celsius=round(egt_margin, 2),
            egt_degradation_pct=round(egt_deg_pct, 2),
            hpc_efficiency_loss_pct=round(hpc_loss, 2),
            hpt_efficiency_loss_pct=round(hpt_loss, 2),
            disk_crack_length_mm=round(crack_mm, 3),
            critical_crack_length_mm=specs.critical_crack_length_mm,
            crack_growth_rate_mm_per_cycle=float(f"{da_dn:.4e}"),
            stress_intensity_range_mpa_sqrt_m=round(delta_k, 2),
            weibull_reliability_rt=round(r_t, 4),
            hazard_rate_per_cycle=float(f"{h_t:.4e}"),
            rul_cycles_remaining=rul_cycles,
            maintenance_status=status,
            maintenance_action_recommended=action,
            avoided_aog_savings_usd=round(avoided_cost, 2),
            cryptographic_diagnosis_digest=digest_sha256,
            timestamp=timestamp_str,
        )

    def get_fleet_overview(self) -> Dict[str, Any]:
        """
        Produces a synthetic airline fleet monitoring deck covering 12 commercial engines.
        """
        fleet_engines = [
            ("ESN-LEAP-98421", TurbofanEngineModel.CFM_LEAP_1A, 6800),
            ("ESN-LEAP-98422", TurbofanEngineModel.CFM_LEAP_1A, 4200),
            ("ESN-LEAP-98423", TurbofanEngineModel.CFM_LEAP_1A, 11400),
            ("ESN-LEAP-98424", TurbofanEngineModel.CFM_LEAP_1A, 1800),
            ("ESN-GE90-70110", TurbofanEngineModel.GE90_115B, 8200),
            ("ESN-GE90-70111", TurbofanEngineModel.GE90_115B, 13800),
            ("ESN-GE90-70112", TurbofanEngineModel.GE90_115B, 3100),
            ("ESN-GE90-70113", TurbofanEngineModel.GE90_115B, 9500),
            ("ESN-KAV-3501", TurbofanEngineModel.KAVERI_GTX_35VS, 2400),
            ("ESN-KAV-3502", TurbofanEngineModel.KAVERI_GTX_35VS, 5900),
            ("ESN-KAV-3503", TurbofanEngineModel.KAVERI_GTX_35VS, 1100),
            ("ESN-KAV-3504", TurbofanEngineModel.KAVERI_GTX_35VS, 7200),
        ]

        diagnoses = []
        total_savings = 0.0
        critical_count = 0

        for esn, model, cycles in fleet_engines:
            diag = self.diagnose_engine(model, cycles, esn)
            diagnoses.append(asdict(diag))
            total_savings += diag.avoided_aog_savings_usd
            if "CRITICAL" in diag.maintenance_status or "EXPEDITE" in diag.maintenance_status:
                critical_count += 1

        mean_rul = sum(d["rul_cycles_remaining"] for d in diagnoses) / len(diagnoses)

        return {
            "fleet_id": "FLEET-SOVEREIGN-GLOBAL-01",
            "total_engines_monitored": len(fleet_engines),
            "engines_in_nominal_service": len(fleet_engines) - critical_count,
            "engines_requiring_inspection": critical_count,
            "fleet_mean_rul_cycles": round(mean_rul, 1),
            "total_avoided_aog_savings_usd": round(total_savings, 2),
            "engines": diagnoses,
        }
