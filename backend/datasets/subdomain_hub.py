"""
AASI Subdomain Dataset & Aerospace Benchmark Hub.
Provides standardized catalog schemas, reference datasets, benchmark challenge definitions,
and domain-specific evaluation metrics across the 5 core aerospace research domains:
1. Aerodynamics & Fluid Dynamics
2. Flight Dynamics & Autonomous Control
3. Structural Health Monitoring (SHM)
4. Autonomy & Computer Vision
5. Mission Planning & Trajectory Optimization
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any
import numpy as np
from pydantic import BaseModel, Field


class AerospaceSubdomain(str, Enum):
    AERODYNAMICS = "AERODYNAMICS_FLUID_DYNAMICS"
    FLIGHT_DYNAMICS = "FLIGHT_DYNAMICS_CONTROL"
    SHM = "STRUCTURAL_HEALTH_MONITORING"
    AUTONOMY_VISION = "AUTONOMY_COMPUTER_VISION"
    MISSION_PLANNING = "MISSION_PLANNING_OPTIMIZATION"


class BenchmarkChallenge(BaseModel):
    challenge_id: str
    subdomain: AerospaceSubdomain
    title: str
    description: str
    reference_dataset: str
    input_features: List[str]
    target_metrics: List[str]
    baseline_algorithm: str
    baseline_score: float
    metric_unit: str


class SubdomainCatalogItem(BaseModel):
    dataset_id: str
    subdomain: AerospaceSubdomain
    name: str
    provider: str
    licensing: str
    sample_count: int
    features: List[str]
    description: str
    download_url_or_ref: str
    sample_data: Dict[str, Any] = Field(default_factory=dict)


class AerospaceSubdomainHub:
    """Central registry and metric evaluation engine for aerospace research benchmarks."""

    _CATALOG: Dict[str, SubdomainCatalogItem] = {}
    _CHALLENGES: Dict[str, BenchmarkChallenge] = {}

    @classmethod
    def initialize_catalog(cls):
        """Populates the 5 aerospace research subdomain datasets and benchmarks."""
        if cls._CATALOG:
            return

        # ── 1. Aerodynamics & Fluid Dynamics ──
        cls._CATALOG["AERO-NASA-CRM"] = SubdomainCatalogItem(
            dataset_id="AERO-NASA-CRM",
            subdomain=AerospaceSubdomain.AERODYNAMICS,
            name="NASA Common Research Model (CRM) Transonic Wind Tunnel Polar",
            provider="NASA Langley Research Center",
            licensing="Public Domain / NASA Technical Report",
            sample_count=1200,
            features=["Mach", "Angle_of_Attack_deg", "Reynolds_Number", "CL", "CD", "CM", "Cp_distribution"],
            description="High-resolution wind tunnel and CFD validation baseline for transport wing-body-tail configurations at M=0.85.",
            download_url_or_ref="https://commonresearchmodel.larc.nasa.gov/",
            sample_data={
                "mach": 0.85,
                "reynolds": 5e6,
                "polar": [
                    {"alpha_deg": 0.0, "cl": 0.224, "cd": 0.0182, "cm": -0.041},
                    {"alpha_deg": 2.0, "cl": 0.448, "cd": 0.0245, "cm": -0.065},
                    {"alpha_deg": 4.0, "cl": 0.652, "cd": 0.0381, "cm": -0.089}
                ]
            }
        )

        cls._CATALOG["AERO-UIUC-AIRFOIL"] = SubdomainCatalogItem(
            dataset_id="AERO-UIUC-AIRFOIL",
            subdomain=AerospaceSubdomain.AERODYNAMICS,
            name="UIUC Applied Aerodynamics Low-Speed Airfoil Polar Database",
            provider="University of Illinois at Urbana-Champaign",
            licensing="Open Research Use (Selig et al.)",
            sample_count=1550,
            features=["alpha_deg", "Cl", "Cd", "Cm", "Re"],
            description="Experimental low-Reynolds number (Re = 60,000 to 500,000) wind tunnel polars for UAV and glider airfoils.",
            download_url_or_ref="https://m-selig.ae.illinois.edu/ads/coord_database.html",
            sample_data={"profiles_indexed": ["NACA 0012", "NACA 2412", "NACA 4412", "Clark Y", "Eppler 387"]}
        )

        cls._CATALOG["AERO-NASA-CMAPSS"] = SubdomainCatalogItem(
            dataset_id="AERO-NASA-CMAPSS",
            subdomain=AerospaceSubdomain.AERODYNAMICS,
            name="NASA Turbofan Engine Degradation Simulation (C-MAPSS)",
            provider="NASA Ames Prognostics Center of Excellence",
            licensing="NASA Open Source Agreement",
            sample_count=21820,
            features=["Engine_ID", "Cycle", "Fan_Speed_rpm", "Core_Temp_K", "Bypass_Ratio", "Remaining_Useful_Life"],
            description="Run-to-failure degradation trajectory simulations of commercial turbofan engines under operational flight regimes.",
            download_url_or_ref="https://data.nasa.gov/dataset/C-MAPSS-Aircraft-Engine-Simulator-Data",
            sample_data={"sensors_monitored": 21, "simulated_subsystems": ["HPT", "LPT", "Combustor", "Fan"]}
        )

        # ── 2. Flight Dynamics & Control ──
        cls._CATALOG["FLIGHT-OPENACR-TELEMETRY"] = SubdomainCatalogItem(
            dataset_id="FLIGHT-OPENACR-TELEMETRY",
            subdomain=AerospaceSubdomain.FLIGHT_DYNAMICS,
            name="OpenAirlines / OpenACR Real Flight Telemetry Logs",
            provider="Open Aerospace Telemetry Consortium",
            licensing="Creative Commons Attribution 4.0",
            sample_count=85000,
            features=["timestamp_s", "pitch_deg", "roll_deg", "yaw_deg", "p_rad_s", "q_rad_s", "r_rad_s", "airspeed_mps", "altitude_m"],
            description="6-DoF sensor logs of fixed-wing UAV maneuvers, wind-gust responses, and autopilot waypoint tracking.",
            download_url_or_ref="https://github.com/open-aero/openacr-telemetry",
            sample_data={"sampling_rate_hz": 50, "controllers_supported": ["PX4_v1.14", "ArduPilot_v4.4"]}
        )

        # ── 3. Structural Health Monitoring (SHM) ──
        cls._CATALOG["SHM-NASA-CNDE"] = SubdomainCatalogItem(
            dataset_id="SHM-NASA-CNDE",
            subdomain=AerospaceSubdomain.SHM,
            name="NASA CNDE Wing Spar Fatigue & Crack Vibration Benchmark",
            provider="NASA Center for Nondestructive Evaluation",
            licensing="Public Domain",
            sample_count=4200,
            features=["sensor_id", "strain_microepsilon", "accel_z_g", "frequency_spectrum", "damage_state"],
            description="Multi-sensor dynamic strain and acoustic emission data for aluminum and composite wing spars subjected to cyclic fatigue.",
            download_url_or_ref="https://cnde.larc.nasa.gov/benchmarks",
            sample_data={"damage_classes": ["UNDAMAGED", "MINOR_CRACK_1MM", "CRACK_5MM", "THROUGH_DELAMINATION"]}
        )

        # ── 4. Autonomy & Computer Vision ──
        cls._CATALOG["AUTO-AIRSIM-DRONE-VISION"] = SubdomainCatalogItem(
            dataset_id="AUTO-AIRSIM-DRONE-VISION",
            subdomain=AerospaceSubdomain.AUTONOMY_VISION,
            name="Microsoft AirSim Synthetic Autonomous Drone Navigation Suite",
            provider="Microsoft Research / Community",
            licensing="MIT License",
            sample_count=15000,
            features=["rgb_image", "depth_map", "optical_flow", "imu_accel", "obstacle_bounding_boxes"],
            description="Synthetic high-fidelity urban and forest flight trajectories for autonomous obstacle avoidance and visual SLAM.",
            download_url_or_ref="https://github.com/microsoft/AirSim",
            sample_data={"resolution": "1920x1080", "modalities": ["RGB", "Depth", "Segmentation", "IMU"]}
        )

        # ── 5. Mission Planning & Trajectory ──
        cls._CATALOG["MISSION-LEO-J2-ORBIT"] = SubdomainCatalogItem(
            dataset_id="MISSION-LEO-J2-ORBIT",
            subdomain=AerospaceSubdomain.MISSION_PLANNING,
            name="LEO Satellite Constellation J2 Orbit & Ground Contact Schedule",
            provider="AASI Orbital Mechanics Engine",
            licensing="Apache License 2.0",
            sample_count=5000,
            features=["semi_major_axis_km", "eccentricity", "inclination_deg", "raan_deg", "eclipse_duration_s", "ground_station_pass_min"],
            description="Secular nodal precession (dRAAN/dt) and cylindrical umbra shadow calculations for Earth observation constellations.",
            download_url_or_ref="https://celestrak.org/",
            sample_data={"reference_epoch": "2026-10-28T00:00:00Z", "perturbations": ["J2_Zonal_Harmonic", "Atmospheric_Drag"]}
        )

        # ── Benchmark Challenges ──
        cls._CHALLENGES["CHALLENGE-AERO-LIFT-DRAG"] = BenchmarkChallenge(
            challenge_id="CHALLENGE-AERO-LIFT-DRAG",
            subdomain=AerospaceSubdomain.AERODYNAMICS,
            title="Fast Transonic Airfoil Lift & Drag Divergence Prediction",
            description="Predict CL and CD across M in [0.6, 0.85] and alpha in [-2, 8] with RMSE < 0.015 and inference latency < 2ms.",
            reference_dataset="AERO-NASA-CRM",
            input_features=["camber", "thickness", "alpha_deg", "mach", "reynolds"],
            target_metrics=["RMSE_CL", "RMSE_CD", "Max_Residual", "Latency_ms"],
            baseline_algorithm="Polynomial Ridge / Vortex Lattice Surrogate",
            baseline_score=0.0124,
            metric_unit="RMSE"
        )

        cls._CHALLENGES["CHALLENGE-SHM-DAMAGE-CLASSIFICATION"] = BenchmarkChallenge(
            challenge_id="CHALLENGE-SHM-DAMAGE-CLASSIFICATION",
            subdomain=AerospaceSubdomain.SHM,
            title="Composite Wing Spar Delamination & Crack Detection",
            description="Classify damage state from 1000Hz vibration accelerometer signals under noisy wind-gust conditions.",
            reference_dataset="SHM-NASA-CNDE",
            input_features=["rms", "kurtosis", "dominant_frequency_hz", "peak_to_peak"],
            target_metrics=["F1_Score", "False_Positive_Rate", "Classification_Accuracy"],
            baseline_algorithm="Spectral Kurtosis + Random Forest",
            baseline_score=0.942,
            metric_unit="F1_Score"
        )

    @classmethod
    def list_datasets(cls, subdomain: Optional[AerospaceSubdomain] = None) -> List[Dict[str, Any]]:
        cls.initialize_catalog()
        res = []
        for item in cls._CATALOG.values():
            if subdomain is None or item.subdomain == subdomain:
                res.append(item.model_dump())
        return res

    @classmethod
    def get_dataset(cls, dataset_id: str) -> Optional[SubdomainCatalogItem]:
        cls.initialize_catalog()
        return cls._CATALOG.get(dataset_id)

    @classmethod
    def list_challenges(cls) -> List[Dict[str, Any]]:
        cls.initialize_catalog()
        return [c.model_dump() for c in cls._CHALLENGES.values()]

    @classmethod
    def evaluate_benchmark_submission(
        cls, challenge_id: str, y_true: np.ndarray, y_pred: np.ndarray
    ) -> Dict[str, Any]:
        """Calculates standard domain metrics for challenge evaluation."""
        cls.initialize_catalog()
        challenge = cls._CHALLENGES.get(challenge_id)
        if not challenge:
            raise ValueError(f"Challenge '{challenge_id}' not found.")

        rmse = float(np.sqrt(np.mean((y_true - y_pred) ** 2)))
        mae = float(np.mean(np.abs(y_true - y_pred)))
        ss_res = np.sum((y_true - y_pred) ** 2)
        ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
        r2 = 1.0 - (ss_res / ss_tot) if ss_tot > 0 else 1.0

        beats_baseline = rmse < challenge.baseline_score

        return {
            "challenge_id": challenge_id,
            "title": challenge.title,
            "rmse": round(rmse, 5),
            "mae": round(mae, 5),
            "r2_score": round(float(r2), 4),
            "baseline_score": challenge.baseline_score,
            "beats_baseline": beats_baseline,
            "verdict": "LEADERBOARD_QUALIFIED" if beats_baseline else "BELOW_BASELINE_THRESHOLD"
        }
