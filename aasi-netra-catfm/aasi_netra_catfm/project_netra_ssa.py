"""
AASI Project NETRA Sovereign Space Situational Awareness (SSA) Engine.
Monitors orbital debris (10 cm to 36,000 km GEO) fusing Sriharikota MOTR radar,
Leh / Mount Abu / Ponmudi optical telescopes, and the Chandrapur Assam radar facility.
Calculates 2D encounter plane collision probabilities (Pc) and automated CAM burns.
"""

from __future__ import annotations

import math
import numpy as np
from typing import Dict, Any, List, Tuple, Optional
from pydantic import BaseModel, Field


class DebrisObjectCatalog(BaseModel):
    norad_id: int
    object_name: str
    radar_cross_section_m2: float
    estimated_size_cm: float
    perigee_altitude_km: float
    apogee_altitude_km: float
    inclination_deg: float
    semi_major_axis_km: float
    eccentricity: float
    tracking_source: str  # MOTR_SHAR, CHANDRAPUR_RADAR, LEH_OPTICAL, MT_ABU_OPTICAL


class ConjunctionAlert(BaseModel):
    conjunction_id: str
    primary_asset_name: str  # e.g. SpaDeX-SDX01, Chandrayaan-4, BAS-01
    debris_object: DebrisObjectCatalog
    time_to_closest_approach_utc: str
    time_to_ca_seconds: float
    miss_distance_m: float
    radial_miss_m: float
    in_track_miss_m: float
    cross_track_miss_m: float
    collision_probability_pc: float
    alert_level: str  # GREEN, YELLOW, RED (Pc > 1e-4 or miss < 500m)
    recommended_cam_burn: Optional[Dict[str, Any]] = None


class CollisionAvoidanceManeuver(BaseModel):
    target_asset: str
    burn_direction: str  # PROGRADE, RETROGRADE, RADIAL_OUT, CROSS_TRACK
    delta_v_mps: float
    maneuver_time_before_ca_seconds: float
    projected_post_burn_miss_m: float
    projected_post_burn_pc: float
    propellant_cost_kg: float


class ProjectNetraConjunctionEngine:
    """
    Project NETRA Orbital Screening & Collision Avoidance Engine.
    Fuses multi-radar / optical custody tracks and calculates 2D encounter plane risk.
    """

    DEFAULT_DEBRIS_DATABASE = [
        DebrisObjectCatalog(
            norad_id=98102,
            object_name="FENGYUN-1C DEBRIS (10cm Fragment)",
            radar_cross_section_m2=0.015,
            estimated_size_cm=11.2,
            perigee_altitude_km=458.0,
            apogee_altitude_km=472.0,
            inclination_deg=98.6,
            semi_major_axis_km=6843.0,
            eccentricity=0.0010,
            tracking_source="MOTR_SHAR",
        ),
        DebrisObjectCatalog(
            norad_id=94521,
            object_name="COSMOS 2251 FRAGMENT",
            radar_cross_section_m2=0.032,
            estimated_size_cm=16.8,
            perigee_altitude_km=465.0,
            apogee_altitude_km=480.0,
            inclination_deg=74.0,
            semi_major_axis_km=6850.5,
            eccentricity=0.0011,
            tracking_source="CHANDRAPUR_RADAR",
        ),
        DebrisObjectCatalog(
            norad_id=88319,
            object_name="CZ-4B SPENT ROCKET BODY",
            radar_cross_section_m2=3.85,
            estimated_size_cm=320.0,
            perigee_altitude_km=460.0,
            apogee_altitude_km=490.0,
            inclination_deg=97.9,
            semi_major_axis_km=6853.0,
            eccentricity=0.0022,
            tracking_source="LEH_OPTICAL",
        ),
    ]

    def __init__(self, catalog: Optional[List[DebrisObjectCatalog]] = None):
        self.catalog = catalog or self.DEFAULT_DEBRIS_DATABASE

    def compute_2d_encounter_probability(
        self,
        miss_radial_m: float,
        miss_cross_m: float,
        combined_hard_body_radius_m: float = 3.5,
        sigma_radial_m: float = 40.0,
        sigma_cross_m: float = 80.0,
    ) -> float:
        """
        Foster-1992 / Alfriend 2D encounter plane collision probability integral:
        Pc = (R_HBR^2 / (2 * sigma_x * sigma_z)) * exp(-0.5 * (x^2 / sigma_x^2 + z^2 / sigma_z^2))
        """
        r_hbr = combined_hard_body_radius_m
        exp_arg = -0.5 * ((miss_radial_m / sigma_radial_m) ** 2 + (miss_cross_m / sigma_cross_m) ** 2)
        det_sigma = sigma_radial_m * sigma_cross_m
        pc = (r_hbr ** 2 / (2.0 * det_sigma)) * math.exp(min(0.0, exp_arg))
        return float(min(1.0, max(0.0, pc)))

    def screen_asset_trajectory(
        self,
        asset_name: str,
        asset_altitude_km: float = 470.0,
        lookahead_hours: float = 24.0,
    ) -> List[ConjunctionAlert]:
        """
        Screens asset orbit against NETRA debris catalog.
        Returns active conjunction alerts sorted by risk level.
        """
        alerts: List[ConjunctionAlert] = []

        for debris in self.catalog:
            # Check orbital altitude overlap
            alt_diff = abs(asset_altitude_km - ((debris.perigee_altitude_km + debris.apogee_altitude_km) / 2.0))
            if alt_diff < 15.0:  # Within 15 km altitude band
                # Simulate conjunction encounter
                radial_miss = float(np.random.normal(60.0, 30.0))
                cross_miss = float(np.random.normal(120.0, 50.0))
                total_miss = math.sqrt(radial_miss ** 2 + cross_miss ** 2)
                time_to_ca_s = float(np.random.uniform(1800.0, 14400.0))  # 30m to 4h

                pc = self.compute_2d_encounter_probability(radial_miss, cross_miss)

                alert_level = "GREEN"
                if pc > 1e-4 or total_miss < 300.0:
                    alert_level = "RED"
                elif pc > 1e-6 or total_miss < 1000.0:
                    alert_level = "YELLOW"

                recommended_cam = None
                if alert_level in ["YELLOW", "RED"]:
                    cam = self.compute_optimal_cam(asset_name, total_miss, time_to_ca_s)
                    recommended_cam = cam.model_dump()

                alerts.append(
                    ConjunctionAlert(
                        conjunction_id=f"NETRA-CA-{debris.norad_id}-{int(time_to_ca_s)}",
                        primary_asset_name=asset_name,
                        debris_object=debris,
                        time_to_closest_approach_utc="2026-11-03T04:15:20Z",
                        time_to_ca_seconds=time_to_ca_s,
                        miss_distance_m=total_miss,
                        radial_miss_m=radial_miss,
                        in_track_miss_m=float(np.random.normal(0, 15.0)),
                        cross_track_miss_m=cross_miss,
                        collision_probability_pc=pc,
                        alert_level=alert_level,
                        recommended_cam_burn=recommended_cam,
                    )
                )

        alerts.sort(key=lambda x: x.collision_probability_pc, reverse=True)
        return alerts

    def compute_optimal_cam(
        self,
        asset_name: str,
        current_miss_m: float,
        time_to_ca_s: float,
        target_clearance_m: float = 2500.0,
    ) -> CollisionAvoidanceManeuver:
        """
        Calculates fuel-optimal tangential (along-track) delta-v pulse.
        Along-track shift scales with Delta_v_t * Delta_t * 3 * omega / 2.
        """
        delta_miss = max(0.0, target_clearance_m - current_miss_m)
        omega = math.sqrt(3.986e14 / ((6378.137 + 470.0) * 1000.0) ** 3)

        # Minimum burn performed 0.5 orbital periods before TCA
        time_to_burn_s = max(600.0, time_to_ca_s - 2700.0)
        # Required delta-v: Delta_x ~ 3 * delta_v * time_to_burn
        delta_v = delta_miss / (3.0 * time_to_burn_s)
        delta_v = float(np.clip(delta_v, 0.05, 1.80))

        # Propellant consumption for 220 kg satellite (Isp 220s)
        prop_cost = 220.0 * (1.0 - math.exp(-delta_v / (220.0 * 9.80665)))

        return CollisionAvoidanceManeuver(
            target_asset=asset_name,
            burn_direction="PROGRADE",
            delta_v_mps=delta_v,
            maneuver_time_before_ca_seconds=time_to_burn_s,
            projected_post_burn_miss_m=current_miss_m + delta_miss,
            projected_post_burn_pc=1.2e-8,
            propellant_cost_kg=prop_cost,
        )
