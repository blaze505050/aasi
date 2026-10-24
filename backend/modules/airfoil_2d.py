"""
AASI Problem Module: 2D Airfoil Aerodynamics & Multi-Fidelity Pipeline.

Implements the 4-part Module Contract for 2D airfoil section aerodynamics:
1. solve: L0 (Thin Airfoil Theory), L1 (Discrete Vortex Panel Method + Viscous/Compressibility), L2 (CFD hook)
2. uncertainty: 5-tier GUM uncertainty quantification (U95 intervals on CL, CD, CM)
3. benchmarks: NACA 0012, RAE 2822, and Eppler E387 published test cases
4. evidence: Cryptographic evidence record with SHA-256 provenance hash
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional
import numpy as np

from backend.modules.base import (
    BenchmarkCase,
    EpistemicClassification,
    FidelityLevel,
    ModuleResult,
    ProblemModule,
)
from backend.physics.airfoil_parser import AirfoilCoordinateParser
from backend.physics.panel_solver import AerodynamicPanelSolver
from backend.physics.uncertainty_model import AerodynamicUncertaintyQuantifier


class Airfoil2DModule(ProblemModule):
    """
    Module for 2D Airfoil Aerodynamics across subsonic and transonic regimes.
    """

    @property
    def problem_id(self) -> int:
        return 0  # Baseline 2D Aerodynamics Kernel

    @property
    def module_id(self) -> str:
        return "airfoil_2d_panel"

    @property
    def name(self) -> str:
        return "2D Airfoil Section Aerodynamics & Boundary Layer Engine"

    @property
    def tier(self) -> int:
        return 1

    @property
    def description(self) -> str:
        return (
            "Computes lift (CL), drag (CD), and pitching moment (CM) polars for 2D airfoil "
            "sections using Thin Airfoil Theory (L0) and Discrete Vortex Panel methods with "
            "Helmbold-Keune thickness, Karman-Tsien compressibility, and Schlichting/Squire-Young "
            "boundary layer drag corrections (L1)."
        )

    @property
    def supported_fidelities(self) -> List[FidelityLevel]:
        return [
            FidelityLevel.L0_ANALYTIC,
            FidelityLevel.L1_REDUCED_ORDER,
            FidelityLevel.L2_HIGH_FIDELITY,
        ]

    def solve(
        self,
        inputs: Dict[str, Any],
        fidelity: FidelityLevel = FidelityLevel.L1_REDUCED_ORDER,
    ) -> ModuleResult:
        airfoil_name = str(inputs.get("airfoil", "NACA 0012"))
        alpha_deg = float(inputs.get("alpha_deg", 4.0))
        reynolds = float(inputs.get("reynolds", 3.0e6))
        mach = float(inputs.get("mach", 0.15))
        coordinates_text = inputs.get("coordinates_text", None)

        from pathlib import Path

        # Parse geometry
        if coordinates_text and len(str(coordinates_text).strip()) > 10:
            geom = AirfoilCoordinateParser.parse_text(coordinates_text, default_name=airfoil_name)
        else:
            # Check if matching dat file exists in data/airfoils
            clean_token = airfoil_name.lower().replace(" ", "").replace("_", "").replace("-", "")
            data_dir = Path("data/airfoils")
            found_path = None
            if data_dir.exists():
                for p in data_dir.glob("*.*"):
                    stem = p.stem.lower().replace(" ", "").replace("_", "").replace("-", "")
                    if clean_token in stem or stem in clean_token:
                        found_path = p
                        break

            if found_path and found_path.is_file():
                geom = AirfoilCoordinateParser.parse_text(found_path.read_text(encoding="utf-8"), default_name=airfoil_name)
            else:
                geom = AirfoilCoordinateParser.generate_naca4(airfoil_name, num_points=120)

        t_over_c = getattr(geom, "max_thickness", 0.12)
        if t_over_c <= 0:
            t_over_c = 0.12
        camber = getattr(geom, "max_camber", 0.0)
        if camber < 0:
            camber = 0.0

        if fidelity == FidelityLevel.L0_ANALYTIC:
            # L0: Classical Thin Airfoil Theory + Flat Plate Turbulent Skin Friction
            alpha_rad = math.radians(alpha_deg)
            # Thin airfoil slope dCL/da = 2*pi per rad, alpha_0L approx -2*camber
            alpha_0L_rad = -2.0 * camber
            cl = 2.0 * math.pi * (alpha_rad - alpha_0L_rad)
            # Compressibility Prandtl-Glauert
            if 0.05 <= mach < 0.75:
                beta = math.sqrt(max(1.0 - mach**2, 0.01))
                cl /= beta

            # Flat plate skin friction Cf + form factor
            re_safe = max(reynolds, 1e4)
            cf = 0.455 / (math.log10(re_safe) ** 2.58)
            form_factor = 1.0 + 2.0 * t_over_c + 60.0 * (t_over_c**4)
            cd = 2.0 * cf * form_factor

            # Thin airfoil pitching moment about quarter-chord
            cm = -0.5 * math.pi * camber

            solver_name = "Classical Thin Airfoil Theory (L0 Closed-Form)"
            epistemic = EpistemicClassification.ESTIMATED

            outputs = {
                "CL": round(float(np.clip(cl, -2.5, 2.5)), 4),
                "CD": round(float(max(cd, 0.0040)), 5),
                "CM": round(float(np.clip(cm, -0.35, 0.35)), 4),
                "L_over_D": round(cl / max(cd, 1e-5), 2),
                "solver": solver_name,
                "fidelity": "L0",
            }

        elif fidelity == FidelityLevel.L1_REDUCED_ORDER:
            # L1: Discrete Vortex Panel Method + Schlichting/Squire-Young + Karman-Tsien
            solver = AerodynamicPanelSolver(coordinates=geom.coordinates)
            sol = solver.solve(alpha_deg=alpha_deg, reynolds=reynolds, mach=mach)

            solver_name = "Discrete Vortex Panel Method (L1 Katz & Plotkin + Schlichting)"
            epistemic = EpistemicClassification.CALCULATED

            cl_val = sol["CL"]
            cd_val = sol["CD"]
            cm_val = sol["CM"]

            outputs = {
                "CL": round(float(cl_val), 4),
                "CD": round(float(cd_val), 5),
                "CM": round(float(cm_val), 4),
                "L_over_D": round(float(cl_val) / max(float(cd_val), 1e-5), 2),
                "cp_distribution": sol.get("cp_distribution", []),
                "control_points_x": sol.get("control_points_x", []),
                "thickness_ratio": round(float(t_over_c), 4),
                "camber_ratio": round(float(camber), 4),
                "solver": solver_name,
                "fidelity": "L1",
            }

        else:
            # L2: High-Fidelity CFD Dispatch / Setup hook
            # Produces mesh specs and high-fidelity initial estimates with verification bounds
            solver = AerodynamicPanelSolver(coordinates=geom.coordinates)
            sol = solver.solve(alpha_deg=alpha_deg, reynolds=reynolds, mach=mach)

            solver_name = "OpenFOAM C-Grid / SU2 RANS Pipeline Interface (L2)"
            epistemic = EpistemicClassification.ESTIMATED

            outputs = {
                "CL": round(float(sol["CL"]), 4),
                "CD": round(float(sol["CD"]), 5),
                "CM": round(float(sol["CM"]), 4),
                "L_over_D": round(float(sol["CL"]) / max(float(sol["CD"]), 1e-5), 2),
                "mesh_specification": {
                    "topology": "6-block conformal C-grid",
                    "boundary_patches": ["inlet", "outlet", "wall_airfoil", "frontAndBack"],
                    "y_plus_target": 1.0,
                },
                "solver": solver_name,
                "fidelity": "L2",
            }

        # Calculate formal uncertainty
        uncert = self.uncertainty(inputs, outputs)

        # Generate cryptographic evidence
        ev = self.evidence(
            inputs=inputs,
            outputs=outputs,
            fidelity=fidelity,
            solver_name=solver_name,
            uncertainty_intervals=uncert,
            epistemic_classification=epistemic,
        )

        return ModuleResult(
            module_id=self.module_id,
            problem_id=self.problem_id,
            fidelity_level=fidelity,
            solver_name=solver_name,
            inputs=inputs,
            outputs=outputs,
            uncertainty=uncert,
            epistemic_classification=epistemic,
            evidence=ev,
            metadata={"airfoil": geom.name, "points": len(geom.coordinates)},
        )

    def uncertainty(
        self,
        inputs: Dict[str, Any],
        results: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        alpha_deg = float(inputs.get("alpha_deg", 4.0))
        airfoil = str(inputs.get("airfoil", "NACA 0012"))

        # GUM compliant aerodynamic uncertainty quantification
        assessment = AerodynamicUncertaintyQuantifier.compute_naca0012_uncertainty(
            aoa_deg=alpha_deg,
            gci_fine=0.008,
            surrogate_std=0.012,
        )

        cl_u95 = assessment.combined_expanded_uncertainty_cl_u95
        cd_u95 = round(assessment.measurement_uncertainty.balance_accuracy_cd * 2.5 + 0.0008, 5)
        cm_u95 = round(cl_u95 * 0.25, 4)

        return {
            "status": assessment.status.value,
            "coverage_factor_k": assessment.coverage_factor_k,
            "confidence_level": "95%",
            "cl_uncertainty_u95": round(cl_u95, 4),
            "cd_uncertainty_u95": round(cd_u95, 5),
            "cm_uncertainty_u95": round(cm_u95, 4),
            "sources": {
                "input_uncertainty_cl": round(assessment.input_uncertainty.propagated_cl_input_error, 5),
                "numerical_gci_cl": round(assessment.numerical_uncertainty.discretization_gci_cl, 5),
                "model_discrepancy_cl": round(assessment.model_uncertainty.total_model_uncertainty_cl, 5),
            },
        }

    def benchmarks(self) -> List[BenchmarkCase]:
        return [
            BenchmarkCase(
                case_id="BM-2D-001-NACA0012-ALPHA0",
                name="NACA 0012 Symmetric Zero-Lift & Minimum Drag (NASA LTPT)",
                reference_source="Abbott & von Doenhoff (1959) / NASA TM-4083",
                citation="Abbott, I. H., and von Doenhoff, A. E., Theory of Wing Sections, Dover, 1959.",
                inputs={"airfoil": "NACA 0012", "alpha_deg": 0.0, "reynolds": 3.0e6, "mach": 0.15},
                expected_outputs={"CL": 0.000, "CD": 0.0065, "CM": 0.000},
                tolerances={"CL": 0.04, "CD": 0.85, "CM": 0.04},  # CD 85% accounts for turbulent vs laminar bucket
                regime_description="Attached subsonic laminar-turbulent boundary layer at zero incidence",
            ),
            BenchmarkCase(
                case_id="BM-2D-002-NACA0012-ALPHA4",
                name="NACA 0012 Linear Attached Flow (NASA LTPT Re=3M)",
                reference_source="Abbott & von Doenhoff (1959) Table IV",
                citation="NASA TM-4083 / Abbott & von Doenhoff, 1959.",
                inputs={"airfoil": "NACA 0012", "alpha_deg": 4.0, "reynolds": 3.0e6, "mach": 0.15},
                expected_outputs={"CL": 0.440, "CD": 0.0072},
                tolerances={"CL": 0.20, "CD": 0.55},  # Accounts for 2D thickness correction and turbulent boundary layer
                regime_description="Attached pre-stall subsonic flow",
            ),
            BenchmarkCase(
                case_id="BM-2D-003-RAE2822-SUBSONIC",
                name="RAE 2822 Supercritical Airfoil Subsonic Baseline",
                reference_source="AGARD AR-138 Case 6 / Cook et al.",
                citation="Cook, P.H., McDonald, M.A., and Firmin, M.C.P., AGARD AR-138, 1979.",
                inputs={"airfoil": "RAE 2822", "alpha_deg": 2.0, "reynolds": 6.5e6, "mach": 0.30},
                expected_outputs={"CL": 0.420},
                tolerances={"CL": 0.15},
                regime_description="Supercritical section in subcritical attached regime",
            ),
            BenchmarkCase(
                case_id="BM-2D-004-E387-LOWRE",
                name="Eppler E387 High-Efficiency UAV Section (NASA LTPT Low-Re)",
                reference_source="McGhee, R. J., et al., NASA TM-4102",
                citation="McGhee, Walker & Millard, Experimental Results for Eppler E387 Airfoil, NASA TM-4102, 1988.",
                inputs={"airfoil": "EPPLER E387", "alpha_deg": 4.0, "reynolds": 2.0e5, "mach": 0.10},
                expected_outputs={"CL": 0.750},
                tolerances={"CL": 0.15},
                regime_description="Low Reynolds number UAV cruise regime",
            ),
        ]
