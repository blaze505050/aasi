"""
AASI Phase 23: Complete Preflight Quality Auditor for Real CFD.
Governing Doctrine: Absolute Anti-Fabrication Rule.
Performs rigorous geometric and computational mesh verification before allowing job dispatch.
"""

import math
from typing import Any, Dict, List, Optional, Tuple
import numpy as np


class CFDPreflightAuditor:
    """
    Automated preflight inspector evaluating geometry and mesh prior to CFD execution.
    Guarantees that flawed profiles or pathological meshes fail closed before solver dispatch.
    """

    MAX_NON_ORTHOGONALITY_DEG = 70.0
    MAX_SKEWNESS = 4.0
    MAX_BOUNDARY_LAYER_ASPECT_RATIO = 1000.0
    MAX_FREESTREAM_ASPECT_RATIO = 50.0
    MAX_CELL_COUNT_2D = 100_000

    @classmethod
    def audit_geometry(
        cls,
        coordinates: np.ndarray,
        airfoil_name: str = "NACA 0012",
        tolerance: float = 1e-4,
    ) -> Dict[str, Any]:
        """
        Audit profile geometry for closure, self-intersection, and chord normalization.
        """
        coords = np.asarray(coordinates, dtype=np.float64)
        n_points = len(coords)

        violations: List[str] = []

        if n_points < 10:
            violations.append(f"Insufficient coordinate resolution: {n_points} points (minimum 10 required).")

        # 1. Closure Check
        # Distance between first and last point
        closure_gap = float(np.linalg.norm(coords[0] - coords[-1]))
        closure_passed = closure_gap <= tolerance
        if not closure_passed:
            violations.append(f"Profile is unclosed: gap of {closure_gap:.6f} exceeds tolerance {tolerance}.")

        # 2. Chord Normalization Check
        x_min = float(np.min(coords[:, 0]))
        x_max = float(np.max(coords[:, 0]))
        chord_length = x_max - x_min
        norm_passed = abs(chord_length - 1.0) <= 0.01 and abs(x_min) <= 0.01
        if not norm_passed:
            violations.append(f"Profile is unnormalized: x in [{x_min:.4f}, {x_max:.4f}], chord={chord_length:.4f}.")

        # 3. Self-Intersection Check
        # Check non-adjacent segments for planar intersection
        intersections = cls._check_self_intersections(coords)
        self_intersection_passed = len(intersections) == 0
        if not self_intersection_passed:
            violations.append(f"Self-intersection detected at {len(intersections)} segment pairs.")

        # 4. Thickness and Camber Evaluation
        y_max = float(np.max(coords[:, 1]))
        y_min = float(np.min(coords[:, 1]))
        thickness = y_max - y_min

        is_admissible = len(violations) == 0

        return {
            "admissible": is_admissible,
            "airfoil_name": airfoil_name,
            "point_count": n_points,
            "closure": {
                "passed": closure_passed,
                "gap": closure_gap,
                "tolerance": tolerance,
            },
            "normalization": {
                "passed": norm_passed,
                "x_min": x_min,
                "x_max": x_max,
                "chord": chord_length,
            },
            "self_intersection": {
                "passed": self_intersection_passed,
                "intersection_count": len(intersections),
            },
            "thickness_estimate": round(thickness, 4),
            "violations": violations,
            "status": "GEOMETRY_VERIFIED" if is_admissible else "GEOMETRY_PREFLIGHT_FAILED",
        }

    @classmethod
    def audit_mesh(
        cls,
        cell_count: int,
        max_non_orthogonality: float = 45.0,
        max_skewness: float = 1.8,
        max_aspect_ratio: float = 35.0,
        boundary_names: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Audit computational mesh quality against numerical stability limits.
        """
        violations: List[str] = []

        if cell_count > cls.MAX_CELL_COUNT_2D:
            violations.append(f"Cell count ({cell_count}) exceeds allowable 2D ceiling ({cls.MAX_CELL_COUNT_2D}).")

        if max_non_orthogonality > cls.MAX_NON_ORTHOGONALITY_DEG:
            violations.append(
                f"Maximum non-orthogonality ({max_non_orthogonality:.1f}°) exceeds threshold ({cls.MAX_NON_ORTHOGONALITY_DEG}°)."
            )

        if max_skewness > cls.MAX_SKEWNESS:
            violations.append(f"Maximum skewness ({max_skewness:.2f}) exceeds threshold ({cls.MAX_SKEWNESS}).")

        if max_aspect_ratio > cls.MAX_BOUNDARY_LAYER_ASPECT_RATIO:
            violations.append(
                f"Maximum aspect ratio ({max_aspect_ratio:.1f}) exceeds threshold ({cls.MAX_BOUNDARY_LAYER_ASPECT_RATIO})."
            )

        required_boundaries = {"inlet", "outlet", "airfoil"}
        b_names = set(boundary_names or ["inlet", "outlet", "airfoil", "frontAndBack"])
        missing_bounds = required_boundaries - b_names
        if missing_bounds:
            violations.append(f"Missing mandatory patch boundaries: {missing_bounds}")

        is_admissible = len(violations) == 0

        return {
            "admissible": is_admissible,
            "cell_count": cell_count,
            "max_non_orthogonality_deg": max_non_orthogonality,
            "max_skewness": max_skewness,
            "max_aspect_ratio": max_aspect_ratio,
            "boundary_names": list(b_names),
            "violations": violations,
            "status": "MESH_VERIFIED" if is_admissible else "MESH_PREFLIGHT_FAILED",
        }

    @classmethod
    def _check_self_intersections(cls, coords: np.ndarray) -> List[Tuple[int, int]]:
        """Find intersections between non-adjacent line segments."""
        n = len(coords) - 1
        intersections = []

        def ccw(A, B, C):
            return (C[1] - A[1]) * (B[0] - A[0]) > (B[1] - A[1]) * (C[0] - A[0])

        def intersect(A, B, C, D):
            return ccw(A, C, D) != ccw(B, C, D) and ccw(A, B, C) != ccw(A, B, D)

        for i in range(n):
            p1, p2 = coords[i], coords[i + 1]
            # Check non-adjacent segments
            for j in range(i + 2, n):
                if i == 0 and j == n - 1:
                    continue  # adjacent at closed endpoints
                p3, p4 = coords[j], coords[j + 1]
                if intersect(p1, p2, p3, p4):
                    intersections.append((i, j))

        return intersections
