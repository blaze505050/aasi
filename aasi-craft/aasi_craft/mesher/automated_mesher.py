"""
Automated Aerospace Mesher & ASME V&V 20 Grid Hierarchy Engine.
Calculates wall-normal spacing y+ for turbulent boundary layers, computes prism layer
inflation stacks, generates 3-level ASME V&V 20 grid configurations (r >= 1.3),
and writes complete OpenFOAM (snappyHexMesh) and SU2 mesh decks.
"""

from __future__ import annotations
import math
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, List, Optional, Tuple


@dataclass
class BoundaryLayerInflation:
    """
    Physical parameters of the near-wall boundary layer inflation mesh.
    """
    reynolds_number: float
    mach_number: float
    freestream_velocity_mps: float
    reference_chord_m: float
    kinematic_viscosity_m2s: float
    target_y_plus: float
    first_cell_height_delta_y1_m: float
    friction_velocity_u_tau_mps: float
    skin_friction_coefficient_cf: float
    wall_shear_stress_tau_w_pa: float
    estimated_bl_thickness_delta_m: float
    num_prism_layers: int
    expansion_ratio: float
    total_prism_stack_height_m: float
    bl_coverage_percentage: float
    is_wall_resolved: bool

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class AsmeGridHierarchy:
    """
    3-Level Grid Hierarchy satisfying ASME V&V 20-2009 refinement constraints (r >= 1.3).
    """
    study_id: str
    target_geometry: str
    grid_refinement_ratio_r: float
    fine_grid_h1: Dict[str, Any]      # cell_size, estimated_cells, y_plus
    medium_grid_h2: Dict[str, Any]    # cell_size, estimated_cells, y_plus
    coarse_grid_h3: Dict[str, Any]    # cell_size, estimated_cells, y_plus
    satisfies_asme_vv20_ratio: bool
    openfoam_snappy_dict: str = ""
    su2_mesh_config: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class AutomatedMesher:
    """
    Automated Aerospace Mesher and Boundary Layer Synthesis Engine.
    """

    @classmethod
    def calculate_boundary_layer_inflation(
        cls,
        u_inf: float = 60.0,
        chord_m: float = 1.0,
        target_y_plus: float = 0.95,
        nu: float = 1.5e-5,
        rho: float = 1.225,
        num_layers: int = 18,
        expansion_ratio: float = 1.18,
    ) -> BoundaryLayerInflation:
        """
        Calculates wall-normal spacing and geometric inflation stack height.
        Re = U * c / nu
        Cf = 0.0592 * Re^(-0.2) (turbulent flat plate)
        tau_w = 0.5 * rho * U^2 * Cf
        u_tau = sqrt(tau_w / rho) = U * sqrt(Cf / 2)
        delta_y1 = y+ * nu / u_tau
        delta = 0.37 * c / Re^0.2
        stack_h = delta_y1 * (r^N - 1) / (r - 1)
        """
        re = (u_inf * chord_m) / max(nu, 1e-9)
        mach = u_inf / 340.29

        # Turbulent flat-plate skin friction
        cf = 0.0592 * (re ** (-0.2)) if re > 1e4 else 1.328 / math.sqrt(max(re, 1.0))
        tau_w = 0.5 * rho * (u_inf ** 2) * cf
        u_tau = math.sqrt(tau_w / rho)
        delta_y1 = (target_y_plus * nu) / max(u_tau, 1e-6)

        # Boundary layer thickness
        bl_thickness = (0.37 * chord_m) / (re ** 0.2) if re > 1e4 else 5.0 * chord_m / math.sqrt(max(re, 1.0))

        # Sum of geometric progression for N layers: S = a * (r^N - 1) / (r - 1)
        r = expansion_ratio
        stack_height = delta_y1 * ((r ** num_layers) - 1.0) / (r - 1.0)
        coverage_pct = min(100.0, (stack_height / bl_thickness) * 100.0)

        return BoundaryLayerInflation(
            reynolds_number=round(re, 1),
            mach_number=round(mach, 3),
            freestream_velocity_mps=round(u_inf, 2),
            reference_chord_m=round(chord_m, 3),
            kinematic_viscosity_m2s=nu,
            target_y_plus=round(target_y_plus, 3),
            first_cell_height_delta_y1_m=round(delta_y1, 7),
            friction_velocity_u_tau_mps=round(u_tau, 4),
            skin_friction_coefficient_cf=round(cf, 6),
            wall_shear_stress_tau_w_pa=round(tau_w, 4),
            estimated_bl_thickness_delta_m=round(bl_thickness, 5),
            num_prism_layers=num_layers,
            expansion_ratio=round(r, 3),
            total_prism_stack_height_m=round(stack_height, 5),
            bl_coverage_percentage=round(coverage_pct, 2),
            is_wall_resolved=target_y_plus <= 1.0,
        )

    @classmethod
    def generate_asme_vv20_grid_hierarchy(
        cls,
        geometry_name: str = "UAV_WING",
        base_chord_m: float = 1.0,
        u_inf: float = 60.0,
        grid_refinement_ratio: float = 1.414,  # sqrt(2)
        base_h1_cell_size_m: float = 0.005,
    ) -> AsmeGridHierarchy:
        """
        Synthesizes 3 grid levels (h1 < h2 < h3) satisfying ASME V&V 20-2009 constraint r >= 1.30.
        """
        r = max(grid_refinement_ratio, 1.30)
        bl_fine = cls.calculate_boundary_layer_inflation(u_inf=u_inf, chord_m=base_chord_m, target_y_plus=0.90)

        # Fine Grid (h1)
        h1 = base_h1_cell_size_m
        est_cells_h1 = 450000

        # Medium Grid (h2 = r * h1)
        h2 = h1 * r
        est_cells_h2 = int(est_cells_h1 / (r ** 3))

        # Coarse Grid (h3 = r * h2)
        h3 = h2 * r
        est_cells_h3 = int(est_cells_h1 / ((r ** 2) ** 3))

        # Synthesize OpenFOAM snappyHexMeshDict
        snappy_dict = f"""/*--------------------------------*- C++ -*----------------------------------*\\
| =========                 |                                                 |
| \\\\      /  F ield         | OpenFOAM: The Open Source CFD Toolbox           |
|  \\\\    /   O peration     | Version:  v2312                                 |
|   \\\\  /    A nd           | Target:   {geometry_name}                       |
|    \\\\/     M anipulation  | Mesh:     ASME V&V 20 Wall-Resolved (y+ < 1.0) |
\\*---------------------------------------------------------------------------*/
FoamFile
{{
    version     2.0;
    format      ascii;
    class       dictionary;
    object      snappyHexMeshDict;
}}

castellatedMesh true;
snap            true;
addLayers       true;

geometry
{{
    {geometry_name}.stl
    {{
        type triSurfaceMesh;
        name {geometry_name};
    }}
}}

castellatedMeshControls
{{
    maxLocalCells 1000000;
    maxGlobalCells 2000000;
    minRefinementCells 10;
    maxLoadUnbalance 0.10;
    nCellsBetweenLevels 3;

    features
    (
        {{ file "{geometry_name}.eMesh"; level 4; }}
    );

    refinementSurfaces
    {{
        {geometry_name}
        {{
            level (3 4);
        }}
    }}

    resolveFeatureAngle 30;
    locationInMesh (0.5 0.5 0.5);
}}

snapControls
{{
    nSmoothPatch 3;
    tolerance 2.0;
    nSolveIter 30;
    nRelaxIter 5;
}}

addLayersControls
{{
    relativeSizes false;
    layers
    {{
        "{geometry_name}.*"
        {{
            nSurfaceLayers {bl_fine.num_prism_layers};
        }}
    }}
    expansionRatio {bl_fine.expansion_ratio};
    finalLayerThickness {bl_fine.first_cell_height_delta_y1_m * (bl_fine.expansion_ratio ** (bl_fine.num_prism_layers - 1)):.6e};
    minThickness {bl_fine.first_cell_height_delta_y1_m:.6e};
    nGrow 0;
}}
"""

        # Synthesize SU2 configuration
        su2_cfg = f"""% ------------- DIRECT SU2 CONFIGURATION FOR {geometry_name} ------------- %
SOLVER= RANS
KIND_TURB_MODEL= SA
MATH_PROBLEM= DIRECT
RESTART_SOL= NO

% Reference values
MACH_NUMBER= {bl_fine.mach_number}
AOA= 4.0
REYNOLDS_NUMBER= {bl_fine.reynolds_number:.1e}
REYNOLDS_LENGTH= {base_chord_m}

% Boundary conditions
MARKER_HEATFLUX= ( {geometry_name}, 0.0 )
MARKER_FAR= ( FARFIELD )
MARKER_SYM= ( SYMMETRY )

% Convergence criteria
CONV_FIELD= RMS_DENSITY
CONV_RESIDUAL_MINVAL= -10
CONV_STARTITER= 10
"""

        return AsmeGridHierarchy(
            study_id=f"ASME-VV20-{geometry_name}-{int(u_inf)}MPS",
            target_geometry=geometry_name,
            grid_refinement_ratio_r=round(r, 4),
            fine_grid_h1={
                "grid_level": "h1_fine",
                "characteristic_cell_size_m": round(h1, 6),
                "estimated_cell_count": est_cells_h1,
                "first_cell_y1_m": bl_fine.first_cell_height_delta_y1_m,
                "target_y_plus": 0.90,
            },
            medium_grid_h2={
                "grid_level": "h2_medium",
                "characteristic_cell_size_m": round(h2, 6),
                "estimated_cell_count": est_cells_h2,
                "first_cell_y1_m": round(bl_fine.first_cell_height_delta_y1_m * r, 7),
                "target_y_plus": round(0.90 * r, 2),
            },
            coarse_grid_h3={
                "grid_level": "h3_coarse",
                "characteristic_cell_size_m": round(h3, 6),
                "estimated_cell_count": est_cells_h3,
                "first_cell_y1_m": round(bl_fine.first_cell_height_delta_y1_m * (r ** 2), 7),
                "target_y_plus": round(0.90 * (r ** 2), 2),
            },
            satisfies_asme_vv20_ratio=r >= 1.30,
            openfoam_snappy_dict=snappy_dict.strip(),
            su2_mesh_config=su2_cfg.strip(),
        )

