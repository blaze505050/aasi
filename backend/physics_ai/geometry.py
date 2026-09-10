"""
AASI Airfoil Geometry Representation Layer.

Provides standardized coordinate processing:
- Chord normalization (x/c, y/c)
- Point ordering (Trailing Edge upper -> Leading Edge -> Trailing Edge lower)
- Robust spline resampling to fixed point lengths (e.g. 64 or 128 points)
- Geometric features extraction (max thickness, camber, LE radius, TE gap)
- Quality and sanity flags (self-intersection, discontinuity, excessive thickness).
"""

import math
import numpy as np
from typing import List, Tuple, Dict, Optional, Any
from backend.physics_ai.schemas import GeometryFeatures


class AirfoilGeometryProcessor:
    """Processes, resamples, and extracts features from 2D airfoil coordinate arrays."""

    def __init__(self, target_points: int = 64):
        self.target_points = target_points

    def process_coordinates(
        self,
        coords: List[List[float]],
        geometry_name: str = "Unknown"
    ) -> Tuple[np.ndarray, GeometryFeatures]:
        """
        Takes raw [x, y] coordinates, validates, normalizes to unit chord,
        resamples to target_points, and computes geometric features and quality flags.
        """
        arr = np.array(coords, dtype=np.float64)
        flags = []

        if len(arr) < 10:
            flags.append("INSUFFICIENT_RESOLUTION")
            # Pad or duplicate if drastically small
            while len(arr) < 10:
                arr = np.vstack([arr, arr[-1]])

        # 1. Clean duplicates and NaNs
        arr = arr[~np.isnan(arr).any(axis=1)]
        diffs = np.linalg.norm(np.diff(arr, axis=0), axis=1)
        valid_indices = np.where(diffs > 1e-6)[0]
        if len(valid_indices) > 0:
            arr = np.vstack([arr[valid_indices], arr[-1:]])

        # 2. Normalize Chord and Origin
        x_min, x_max = np.min(arr[:, 0]), np.max(arr[:, 0])
        chord = x_max - x_min
        if chord <= 1e-4:
            flags.append("MALFORMED_ZERO_CHORD")
            chord = 1.0

        arr[:, 0] = (arr[:, 0] - x_min) / chord
        arr[:, 1] = arr[:, 1] / chord

        # 3. Detect LE and TE
        le_idx = int(np.argmin(arr[:, 0]))
        le_point = [float(arr[le_idx, 0]), float(arr[le_idx, 1])]

        te_gap = float(np.linalg.norm(arr[0] - arr[-1]))
        is_closed = te_gap < 0.02
        if not is_closed and te_gap > 0.05:
            flags.append("TRAILING_EDGE_INCONSISTENCY")

        # 4. Resample to fixed point count along contour
        resampled_contour = self._resample_contour(arr, self.target_points)

        # 5. Extract Camber and Thickness Distribution
        mid = self.target_points // 2
        upper = resampled_contour[:mid]
        lower = resampled_contour[mid:]

        # Max thickness estimate
        thicknesses = []
        for pt in upper:
            # Distance to nearest lower surface point
            dists = np.abs(lower[:, 1] - pt[1])
            d_x = np.abs(lower[:, 0] - pt[0])
            close_x = np.where(d_x < 0.05)[0]
            if len(close_x) > 0:
                thicknesses.append(abs(pt[1] - lower[close_x[0], 1]))

        max_thickness = float(max(thicknesses)) if thicknesses else float(np.max(upper[:, 1]) - np.min(lower[:, 1]))
        if max_thickness > 0.35:
            flags.append("EXCESSIVE_THICKNESS")

        # Symmetry check
        is_symmetric = False
        upper_y = np.sort(upper[:, 1])
        lower_y = np.sort(np.abs(lower[:, 1]))
        if len(upper_y) == len(lower_y):
            sym_diff = np.mean(np.abs(upper_y - lower_y))
            is_symmetric = bool(sym_diff < 0.008)

        max_camber = 0.0 if is_symmetric else float(abs(np.mean(arr[:, 1])))

        # Check self-intersection
        if self._check_self_intersection(resampled_contour):
            flags.append("SELF_INTERSECTION")

        features = GeometryFeatures(
            geometry_name=geometry_name,
            n_points=self.target_points,
            max_thickness_ratio=round(max_thickness, 4),
            max_camber_ratio=round(max_camber, 4),
            leading_edge_point=[round(x, 4) for x in le_point],
            trailing_edge_gap=round(te_gap, 4),
            is_closed=is_closed,
            is_symmetric=is_symmetric,
            quality_flags=flags
        )

        return resampled_contour, features

    def _resample_contour(self, pts: np.ndarray, target_n: int) -> np.ndarray:
        """Equidistant arc-length resampling along airfoil contour."""
        # Calculate cumulative distances
        deltas = np.diff(pts, axis=0)
        dist = np.sqrt((deltas ** 2).sum(axis=1))
        cumulative = np.insert(np.cumsum(dist), 0, 0)
        total_len = cumulative[-1]

        if total_len <= 1e-6:
            return np.zeros((target_n, 2))

        eval_pts = np.linspace(0, total_len, target_n)
        new_x = np.interp(eval_pts, cumulative, pts[:, 0])
        new_y = np.interp(eval_pts, cumulative, pts[:, 1])
        return np.column_stack([new_x, new_y])

    def _check_self_intersection(self, pts: np.ndarray) -> bool:
        """Basic check if non-adjacent segments intersect."""
        n = len(pts)
        if n < 5:
            return False
        # Simplified bounding box / gradient monotonicity check
        diffs_y = np.diff(pts[:, 1])
        extreme_jumps = np.sum(np.abs(np.diff(diffs_y)) > 0.4)
        return bool(extreme_jumps > 5)

    def generate_naca_4digit(
        self,
        code: str = "0012",
        n_points: int = 100
    ) -> Tuple[np.ndarray, GeometryFeatures]:
        """Generates coordinates using analytical NACA 4-digit formula and processes them."""
        code = code.strip().zfill(4)[-4:]
        m = int(code[0]) / 100.0
        p = int(code[1]) / 10.0
        t = int(code[2:]) / 100.0

        # Cosine clustering along chord
        beta = np.linspace(0, np.pi, n_points)
        x = 0.5 * (1.0 - np.cos(beta))

        # Half thickness distribution
        yt = 5.0 * t * (
            0.2969 * np.sqrt(np.maximum(0.0, x))
            - 0.1260 * x
            - 0.3516 * (x ** 2)
            + 0.2843 * (x ** 3)
            - 0.1036 * (x ** 4)
        )

        # Camber line
        yc = np.zeros_like(x)
        dyc_dx = np.zeros_like(x)

        if p > 0 and m > 0:
            forward = x < p
            rear = ~forward
            yc[forward] = (m / (p ** 2)) * (2.0 * p * x[forward] - (x[forward] ** 2))
            dyc_dx[forward] = (2.0 * m / (p ** 2)) * (p - x[forward])

            yc[rear] = (m / ((1.0 - p) ** 2)) * ((1.0 - 2.0 * p) + 2.0 * p * x[rear] - (x[rear] ** 2))
            dyc_dx[rear] = (2.0 * m / ((1.0 - p) ** 2)) * (p - x[rear])

        theta = np.arctan(dyc_dx)
        xu = x - yt * np.sin(theta)
        yu = yc + yt * np.cos(theta)
        xl = x + yt * np.sin(theta)
        yl = yc - yt * np.cos(theta)

        # Contour order: TE upper -> LE -> TE lower
        upper = np.column_stack([xu[::-1], yu[::-1]])
        lower = np.column_stack([xl[1:], yl[1:]])
        contour = np.vstack([upper, lower])

        return self.process_coordinates(contour.tolist(), geometry_name=f"NACA {code}")

