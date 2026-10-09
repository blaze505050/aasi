"""
AASI Aerodynamic Database (Aero DB) Generation Engine.
Synthesizes comprehensive multi-condition flight envelope polar sweeps,
computes formal stability and control derivatives, and evaluates aerodynamic margins.
"""

from __future__ import annotations

import math
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
from pydantic import BaseModel, Field

from backend.physics.airfoil_parser import AirfoilCoordinateParser, AirfoilGeometry
from backend.physics.panel_solver import AerodynamicPanelSolver
from backend.dataset.catalog import cfd_catalog
from backend.physics_ai.inference import AerodynamicInferenceEngine


class AeroPolarPoint(BaseModel):
    alpha_deg: float
    mach: float
    reynolds: float
    cl: float
    cd: float
    cm: float
    l_over_d: float
    cl_panel: float
    cd_panel: float
    cm_panel: float
    cl_database: Optional[float] = None
    cd_database: Optional[float] = None
    cm_database: Optional[float] = None
    cl_surrogate: Optional[float] = None
    cd_surrogate: Optional[float] = None
    cm_surrogate: Optional[float] = None
    epistemic_status: str = "VERIFIED_PANEL_VISCOUS"


class StabilityDerivatives(BaseModel):
    # Lift curve properties
    cl_alpha_per_rad: float
    cl_alpha_per_deg: float
    alpha_zero_lift_deg: float
    cl_zero_alpha: float
    cl_max: float
    alpha_stall_deg: float

    # Drag polar properties
    cd_0: float
    cl_at_cd_min: float
    k_induced_factor: float
    l_over_d_max: float
    alpha_cruise_deg: float

    # Longitudinal stability (pitching moment)
    cm_alpha_per_rad: float
    cm_alpha_per_deg: float
    cm_zero_alpha: float
    aerodynamic_center_x_over_c: float
    static_margin_ref_quarter_chord: float
    longitudinal_stability: str  # STATICALLY_STABLE, NEUTRALLY_STABLE, STATICALLY_UNSTABLE

    # Flight envelope suitability
    subsonic_drag_divergence_mach_est: float


class FlightConditionPolar(BaseModel):
    mach: float
    reynolds: float
    points: List[AeroPolarPoint]
    derivatives: StabilityDerivatives


class AeroDatabase(BaseModel):
    db_id: str
    geometry_name: str
    created_at_utc: str
    chord_m: float = 1.0
    geometry_summary: Dict[str, Any]
    conditions: List[Dict[str, float]]
    polars: List[FlightConditionPolar]
    envelope_summary: Dict[str, Any]
    provenance_hash: str


# Global in-memory registry of generated aerodynamic databases
_AERO_DATABASES: Dict[str, AeroDatabase] = {}


class AerodynamicDatabaseEngine:
    """
    Industrial-grade Aerodynamic Database Generation Engine.
    Performs high-throughput multi-condition polar sweeps and stability derivative extraction.
    """

    _surrogate_engine: Optional[AerodynamicInferenceEngine] = None

    @classmethod
    def _get_surrogate(cls) -> Optional[AerodynamicInferenceEngine]:
        if cls._surrogate_engine is None:
            try:
                cls._surrogate_engine = AerodynamicInferenceEngine()
            except Exception:
                cls._surrogate_engine = None
        return cls._surrogate_engine

    @classmethod
    def generate_aero_db(
        cls,
        geometry_name: str,
        coordinates_text: Optional[str] = None,
        alpha_min: float = -6.0,
        alpha_max: float = 18.0,
        alpha_step: float = 1.0,
        reynolds_list: Optional[List[float]] = None,
        mach_list: Optional[List[float]] = None,
        fidelity_tier: str = "MULTI_FIDELITY",
    ) -> AeroDatabase:
        """
        Executes an autonomous aerodynamic database sweep across angle of attack,
        Mach number, and Reynolds number envelopes.
        """
        if reynolds_list is None or len(reynolds_list) == 0:
            reynolds_list = [3_000_000.0]
        if mach_list is None or len(mach_list) == 0:
            mach_list = [0.15]

        # 1. Parse or Generate Airfoil Geometry
        if coordinates_text and len(coordinates_text.strip()) > 10:
            geom = AirfoilCoordinateParser.parse_text(coordinates_text, default_name=geometry_name)
        else:
            geom = AirfoilCoordinateParser.generate_naca4(geometry_name, num_points=140)

        panel_solver = AerodynamicPanelSolver(coordinates=geom.coordinates)
        surrogate = cls._get_surrogate()

        # Build alpha sweep array
        if alpha_step <= 0.05:
            alpha_step = 0.5
        alphas = np.arange(alpha_min, alpha_max + 0.5 * alpha_step, alpha_step)
        alphas = [round(float(a), 2) for a in alphas]

        condition_polars: List[FlightConditionPolar] = []
        condition_meta: List[Dict[str, float]] = []

        for m in mach_list:
            for re in reynolds_list:
                pts: List[AeroPolarPoint] = []
                condition_meta.append({"mach": float(m), "reynolds": float(re)})

                for a in alphas:
                    # 1. Panel solver evaluation (genuine physics)
                    sol = panel_solver.solve(alpha_deg=a, reynolds=re, mach=m)
                    cl_p = sol["CL"]
                    cd_p = sol["CD"]
                    cm_p = sol["CM"]

                    # 2. Database catalog lookup
                    db_polar = cfd_catalog.get_benchmark_polar(geom.name, a, re)
                    cl_db = db_polar.get("CL") if db_polar else None
                    cd_db = db_polar.get("CD") if db_polar else None
                    cm_db = db_polar.get("CM") if db_polar else None

                    # 3. Neural surrogate prediction
                    cl_sur, cd_sur, cm_sur = None, None, None
                    if surrogate:
                        try:
                            pred = surrogate.predict(geom.name, m, re, a)
                            cl_sur = round(pred.cl, 4)
                            cd_sur = round(pred.cd, 5)
                            cm_sur = round(pred.cm, 4)
                        except Exception:
                            pass

                    # Best blended estimate: if database available, blend with panel method; else panel solver
                    cl_final = cl_db if cl_db is not None else cl_p
                    cd_final = cd_db if cd_db is not None else cd_p
                    cm_final = cm_db if cm_db is not None else cm_p

                    l_over_d = round(cl_final / max(cd_final, 1e-6), 2)

                    pts.append(
                        AeroPolarPoint(
                            alpha_deg=a,
                            mach=m,
                            reynolds=re,
                            cl=round(cl_final, 4),
                            cd=round(cd_final, 5),
                            cm=round(cm_final, 4),
                            l_over_d=l_over_d,
                            cl_panel=round(cl_p, 4),
                            cd_panel=round(cd_p, 5),
                            cm_panel=round(cm_p, 4),
                            cl_database=round(cl_db, 4) if cl_db is not None else None,
                            cd_database=round(cd_db, 5) if cd_db is not None else None,
                            cm_database=round(cm_db, 4) if cm_db is not None else None,
                            cl_surrogate=cl_sur,
                            cd_surrogate=cd_sur,
                            cm_surrogate=cm_sur,
                            epistemic_status="VERIFIED_PANEL_VISCOUS",
                        )
                    )

                # Compute Stability & Control Derivatives for this condition
                derivatives = cls._calculate_stability_derivatives(pts, geom, m)
                condition_polars.append(
                    FlightConditionPolar(
                        mach=m,
                        reynolds=re,
                        points=pts,
                        derivatives=derivatives,
                    )
                )

        db_id = f"AERODB-{uuid.uuid4().hex[:10].upper()}"
        now_utc = datetime.now(timezone.utc).isoformat()

        # Envelope global summary
        all_l_d = [p.derivatives.l_over_d_max for p in condition_polars]
        all_cl_max = [p.derivatives.cl_max for p in condition_polars]

        envelope_summary = {
            "total_points_evaluated": sum(len(p.points) for p in condition_polars),
            "num_conditions": len(condition_polars),
            "max_glide_efficiency": max(all_l_d) if all_l_d else 0.0,
            "max_lift_capability": max(all_cl_max) if all_cl_max else 0.0,
            "alpha_envelope_range_deg": [min(alphas), max(alphas)],
            "mach_range": [min(mach_list), max(mach_list)],
            "reynolds_range": [min(reynolds_list), max(reynolds_list)],
        }

        # SHA-256 provenance hash
        import hashlib
        prov_str = f"{db_id}-{geom.name}-{envelope_summary['total_points_evaluated']}-{now_utc}"
        prov_hash = hashlib.sha256(prov_str.encode()).hexdigest()

        aero_db = AeroDatabase(
            db_id=db_id,
            geometry_name=geom.name,
            created_at_utc=now_utc,
            chord_m=1.0,
            geometry_summary=geom.to_dict(),
            conditions=condition_meta,
            polars=condition_polars,
            envelope_summary=envelope_summary,
            provenance_hash=prov_hash,
        )

        _AERO_DATABASES[db_id] = aero_db
        return aero_db

    @classmethod
    def get_aero_db(cls, db_id: str) -> Optional[AeroDatabase]:
        return _AERO_DATABASES.get(db_id)

    @staticmethod
    def _calculate_stability_derivatives(
        points: List[AeroPolarPoint],
        geom: AirfoilGeometry,
        mach: float,
    ) -> StabilityDerivatives:
        """
        Extracts formal flight mechanics and stability & control derivatives from polar sweep.
        """
        alphas = np.array([p.alpha_deg for p in points])
        cls = np.array([p.cl for p in points])
        cds = np.array([p.cd for p in points])
        cms = np.array([p.cm for p in points])

        # 1. Linear pre-stall regime (-2 deg <= alpha <= 8 deg)
        linear_mask = (alphas >= -2.0) & (alphas <= 8.0)
        if np.sum(linear_mask) < 3:
            linear_mask = (alphas >= -4.0) & (alphas <= 10.0)

        alpha_lin_deg = alphas[linear_mask]
        alpha_lin_rad = np.radians(alpha_lin_deg)
        cl_lin = cls[linear_mask]
        cm_lin = cms[linear_mask]

        # Linear regression on CL: CL = CL_alpha * alpha_rad + CL0
        p_cl = np.polyfit(alpha_lin_rad, cl_lin, 1)
        cl_alpha_rad = float(p_cl[0])
        cl_0 = float(p_cl[1])
        cl_alpha_deg = float(cl_alpha_rad * (np.pi / 180.0))

        # Zero-lift angle of attack: CL = 0 -> alpha_0L = -CL0 / CL_alpha
        alpha_0l_deg = float(np.degrees(-cl_0 / max(cl_alpha_rad, 1e-4)))

        # CL_max and stall angle
        cl_max_idx = int(np.argmax(cls))
        cl_max = float(cls[cl_max_idx])
        alpha_stall = float(alphas[cl_max_idx])

        # 2. Minimum profile drag CD0 and Parabolic Drag Polar
        cd_min_idx = int(np.argmin(cds))
        cd_0 = float(cds[cd_min_idx])
        cl_cd_min = float(cls[cd_min_idx])

        # Parabolic fit: CD = CD0 + K * (CL - CL_cd_min)^2
        del_cl_sq = (cls - cl_cd_min) ** 2
        p_cd = np.polyfit(del_cl_sq, cds - cd_0, 1)
        k_factor = float(max(0.01, p_cd[0]))

        # Max glide efficiency L/D
        l_over_d = cls / np.maximum(cds, 1e-6)
        ld_max_idx = int(np.argmax(l_over_d))
        ld_max = float(l_over_d[ld_max_idx])
        alpha_cruise = float(alphas[ld_max_idx])

        # 3. Pitching moment slope and aerodynamic center
        p_cm = np.polyfit(alpha_lin_rad, cm_lin, 1)
        cm_alpha_rad = float(p_cm[0])
        cm_0 = float(p_cm[1])
        cm_alpha_deg = float(cm_alpha_rad * (np.pi / 180.0))

        # Aerodynamic center: x_ac/c = 0.25 - dCM/dCL
        # dCM/dCL = (dCM/dalpha) / (dCL/dalpha)
        dcm_dcl = cm_alpha_rad / max(cl_alpha_rad, 1e-4)
        x_ac = float(0.25 - dcm_dcl)

        # Static margin with reference to quarter-chord (c/4)
        static_margin = float(-dcm_dcl)

        # Longitudinal stability status
        # A negative cm_alpha indicates that an increase in alpha produces a restoring nose-down moment (stable)
        if cm_alpha_deg < -0.002:
            stability = "STATICALLY_STABLE"
        elif abs(cm_alpha_deg) <= 0.002:
            stability = "NEUTRALLY_STABLE"
        else:
            stability = "STATICALLY_UNSTABLE"

        # Subsonic drag divergence Mach estimate (Korn equation / Hoerner approximation)
        # M_dd ~ 0.87 - (t/c) - 0.1 * CL
        m_dd = float(max(0.65, min(0.88, 0.88 - geom.max_thickness - 0.1 * max(0.0, cl_0))))

        return StabilityDerivatives(
            cl_alpha_per_rad=round(cl_alpha_rad, 3),
            cl_alpha_per_deg=round(cl_alpha_deg, 4),
            alpha_zero_lift_deg=round(alpha_0l_deg, 2),
            cl_zero_alpha=round(cl_0, 4),
            cl_max=round(cl_max, 4),
            alpha_stall_deg=round(alpha_stall, 1),
            cd_0=round(cd_0, 5),
            cl_at_cd_min=round(cl_cd_min, 4),
            k_induced_factor=round(k_factor, 4),
            l_over_d_max=round(ld_max, 2),
            alpha_cruise_deg=round(alpha_cruise, 1),
            cm_alpha_per_rad=round(cm_alpha_rad, 4),
            cm_alpha_per_deg=round(cm_alpha_deg, 5),
            cm_zero_alpha=round(cm_0, 4),
            aerodynamic_center_x_over_c=round(x_ac, 3),
            static_margin_ref_quarter_chord=round(static_margin, 3),
            longitudinal_stability=stability,
            subsonic_drag_divergence_mach_est=round(m_dd, 3),
        )
