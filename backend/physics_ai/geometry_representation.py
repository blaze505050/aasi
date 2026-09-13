"""
AASI Phase 20 Geometry-Aware Representation Engine.

Provides mathematically rigorous, deterministic geometric representations:
1. Coordinate normalization, equidistant arc-length resampling, and feature extraction.
2. Cryptographic SHA-256 geometry identity hashing.
3. Multiple experimental representations:
   - Representation A: Low-dimensional engineering descriptors [alpha, Re, t/c, m, p, alpha^2]
   - Representation B: Flattened normalized coordinate vector [x1, y1, ..., xN, yN] + flow conditions
   - Representation C: Surface separation [yu(x), yl(x)] on standard chord abscissae
   - Representation D: Hybrid engineering descriptors + coordinate moments
4. Quantitative geometry contour distance metrics (Hausdorff, Mean Euclidean, Mahalanobis).
"""

from __future__ import annotations
import math
import hashlib
import json
from typing import List, Tuple, Dict, Optional, Any, Union
import numpy as np
from pydantic import BaseModel, Field


class GeometryProfile(BaseModel):
    """Encapsulates raw and normalized geometry with immutable cryptographic identity."""
    geometry_id: str
    geometry_hash: str
    n_points: int
    max_thickness: float
    max_camber: float
    max_camber_pos: float
    leading_edge_point: List[float]
    trailing_edge_gap: float
    is_symmetric: bool
    is_closed: bool
    quality_flags: List[str] = Field(default_factory=list)
    normalized_coordinates: List[List[float]] = Field(default_factory=list)


class GeometryRepresentationEngine:
    """
    Standardizes, hashes, and transforms 2D airfoil contours into
    experimental machine learning representations.
    """

    def __init__(self, target_points: int = 64):
        self.target_points = target_points

    @staticmethod
    def compute_geometry_hash(coords: np.ndarray) -> str:
        """
        Computes an invariant SHA-256 hash from normalized coordinates rounded to 6 decimals.
        Guarantees that identical geometry shapes produce identical hashes.
        """
        rounded = np.round(coords, 6).tolist()
        serialized = json.dumps(rounded, separators=(',', ':'))
        return hashlib.sha256(serialized.encode('utf-8')).hexdigest()

    def process_coordinates(
        self,
        coords: Union[List[List[float]], np.ndarray],
        geometry_name: str = "Unknown"
    ) -> Tuple[np.ndarray, GeometryProfile]:
        """
        Normalizes, resamples, and extracts features and SHA-256 hash from contour coordinates.
        """
        arr = np.array(coords, dtype=np.float64)
        flags: List[str] = []

        if len(arr) < 8:
            flags.append("INSUFFICIENT_RESOLUTION")
            while len(arr) < 8:
                arr = np.vstack([arr, arr[-1]])

        # 1. Clean NaNs and adjacent duplicates
        arr = arr[~np.isnan(arr).any(axis=1)]
        diffs = np.linalg.norm(np.diff(arr, axis=0), axis=1)
        valid_indices = np.where(diffs > 1e-6)[0]
        if len(valid_indices) > 0:
            arr = np.vstack([arr[valid_indices], arr[-1:]])

        # 2. Normalize Chord and Translate Origin to Leading Edge
        x_min, x_max = float(np.min(arr[:, 0])), float(np.max(arr[:, 0]))
        chord = x_max - x_min
        if chord <= 1e-5:
            flags.append("MALFORMED_ZERO_CHORD")
            chord = 1.0

        arr[:, 0] = (arr[:, 0] - x_min) / chord
        arr[:, 1] = arr[:, 1] / chord

        # Ensure origin alignment (minimum x at 0)
        le_idx = int(np.argmin(arr[:, 0]))
        le_point = [float(arr[le_idx, 0]), float(arr[le_idx, 1])]
        arr[:, 1] -= le_point[1]
        le_point[1] = 0.0

        # 3. Resample contour to equidistant arc-length points
        resampled = self._resample_arc_length(arr, self.target_points)

        # 4. Extract camber and thickness distributions
        max_thickness, max_camber, max_camber_pos, is_sym, te_gap, is_closed = (
            self._analyze_profile_metrics(resampled)
        )

        if max_thickness > 0.40:
            flags.append("EXCESSIVE_THICKNESS")
        if max_thickness < 0.02:
            flags.append("UNUSUALLY_THIN")

        # 5. Compute cryptographic geometry identity
        geom_hash = self.compute_geometry_hash(resampled)

        profile = GeometryProfile(
            geometry_id=geometry_name,
            geometry_hash=geom_hash,
            n_points=self.target_points,
            max_thickness=round(max_thickness, 4),
            max_camber=round(max_camber, 4),
            max_camber_pos=round(max_camber_pos, 4),
            leading_edge_point=[round(p, 4) for p in le_point],
            trailing_edge_gap=round(te_gap, 4),
            is_symmetric=is_sym,
            is_closed=is_closed,
            quality_flags=flags,
            normalized_coordinates=resampled.tolist()
        )

        return resampled, profile

    def _resample_arc_length(self, pts: np.ndarray, target_n: int) -> np.ndarray:
        """Equidistant arc-length parametrization along 2D contour."""
        deltas = np.diff(pts, axis=0)
        seg_lens = np.sqrt((deltas ** 2).sum(axis=1))
        cum_len = np.insert(np.cumsum(seg_lens), 0, 0.0)
        total_len = cum_len[-1]

        if total_len <= 1e-7:
            return np.zeros((target_n, 2), dtype=np.float64)

        eval_pts = np.linspace(0.0, total_len, target_n)
        new_x = np.interp(eval_pts, cum_len, pts[:, 0])
        new_y = np.interp(eval_pts, cum_len, pts[:, 1])
        return np.column_stack([new_x, new_y])

    def _analyze_profile_metrics(
        self, pts: np.ndarray
    ) -> Tuple[float, float, float, bool, float, bool]:
        """Calculates thickness, camber, symmetry, and closure metrics."""
        n = len(pts)
        mid = n // 2
        upper = pts[:mid]
        lower = pts[mid:]

        # TE gap
        te_gap = float(np.linalg.norm(pts[0] - pts[-1]))
        is_closed = te_gap < 0.03

        # Approximate upper and lower surfaces evaluated at common x-stations
        eval_x = np.linspace(0.02, 0.98, 50)
        # Interpolate upper surface (sorted by x)
        u_sort = upper[np.argsort(upper[:, 0])]
        l_sort = lower[np.argsort(lower[:, 0])]

        yu = np.interp(eval_x, u_sort[:, 0], u_sort[:, 1])
        yl = np.interp(eval_x, l_sort[:, 0], l_sort[:, 1])

        thickness = np.maximum(0.0, yu - yl)
        max_thickness = float(np.max(thickness)) if len(thickness) > 0 else 0.12

        camber = 0.5 * (yu + yl)
        max_camber_idx = int(np.argmax(np.abs(camber)))
        max_camber = float(np.abs(camber[max_camber_idx]))
        max_camber_pos = float(eval_x[max_camber_idx])

        is_symmetric = bool(max_camber < 0.005)
        if is_symmetric:
            max_camber = 0.0
            max_camber_pos = 0.0

        return max_thickness, max_camber, max_camber_pos, is_symmetric, te_gap, is_closed

    # -------------------------------------------------------------------------
    # 4 Experimental Representations (Directives 6, 36)
    # -------------------------------------------------------------------------

    @staticmethod
    def build_representation_a(
        aoa_deg: float,
        reynolds: float,
        profile: GeometryProfile,
        mach: float = 0.15
    ) -> np.ndarray:
        """
        Representation A (Scalar Engineering Descriptors):
        [alpha, Re, t/c, m, p, alpha^2]
        Matches Phase 19 baseline format.
        """
        return np.array([
            float(aoa_deg),
            float(reynolds),
            float(profile.max_thickness),
            float(profile.max_camber),
            float(profile.max_camber_pos),
            float(aoa_deg ** 2)
        ], dtype=np.float64)

    def build_representation_b(
        self,
        aoa_deg: float,
        reynolds: float,
        profile: GeometryProfile,
        mach: float = 0.15
    ) -> np.ndarray:
        """
        Representation B (Flattened Normalized Coordinate Vector + Flow):
        [x1, y1, x2, y2, ..., xN, yN, alpha, log10(Re), Mach, alpha^2]
        Direct coordinate-level shape token.
        """
        coords = np.array(profile.normalized_coordinates, dtype=np.float64).flatten()
        log_re = math.log10(max(1.0, reynolds))
        flow_tokens = np.array([aoa_deg, log_re, mach, aoa_deg ** 2], dtype=np.float64)
        return np.concatenate([coords, flow_tokens])

    def build_representation_c(
        self,
        aoa_deg: float,
        reynolds: float,
        profile: GeometryProfile,
        mach: float = 0.15,
        n_stations: int = 32
    ) -> np.ndarray:
        """
        Representation C (Separate Upper/Lower Surface Coordinates on Standard Grid):
        [yu(x1), ..., yu(xM), yl(x1), ..., yl(xM), alpha, log10(Re), Mach, alpha^2]
        """
        pts = np.array(profile.normalized_coordinates, dtype=np.float64)
        mid = len(pts) // 2
        upper = pts[:mid]
        lower = pts[mid:]

        u_sort = upper[np.argsort(upper[:, 0])]
        l_sort = lower[np.argsort(lower[:, 0])]

        stations = np.linspace(0.01, 0.99, n_stations)
        yu = np.interp(stations, u_sort[:, 0], u_sort[:, 1])
        yl = np.interp(stations, l_sort[:, 0], l_sort[:, 1])

        log_re = math.log10(max(1.0, reynolds))
        flow_tokens = np.array([aoa_deg, log_re, mach, aoa_deg ** 2], dtype=np.float64)
        return np.concatenate([yu, yl, flow_tokens])

    def build_representation_d(
        self,
        aoa_deg: float,
        reynolds: float,
        profile: GeometryProfile,
        mach: float = 0.15
    ) -> np.ndarray:
        """
        Representation D (Hybrid Engineering Descriptors + Coordinate Moments):
        Combines macro features [alpha, Re, t/c, m, p, alpha^2] with local thickness
        at 5 chord stations [0.1, 0.3, 0.5, 0.7, 0.9] and leading-edge sharpness proxy.
        """
        pts = np.array(profile.normalized_coordinates, dtype=np.float64)
        mid = len(pts) // 2
        upper = pts[:mid]
        lower = pts[mid:]

        u_sort = upper[np.argsort(upper[:, 0])]
        l_sort = lower[np.argsort(lower[:, 0])]

        probe_stations = np.array([0.1, 0.3, 0.5, 0.7, 0.9])
        yu = np.interp(probe_stations, u_sort[:, 0], u_sort[:, 1])
        yl = np.interp(probe_stations, l_sort[:, 0], l_sort[:, 1])
        local_thickness = yu - yl
        local_camber = 0.5 * (yu + yl)

        # Leading edge radius proxy: y_upper at x = 0.01
        le_proxy = float(np.interp(0.01, u_sort[:, 0], u_sort[:, 1]))

        rep_a = self.build_representation_a(aoa_deg, reynolds, profile, mach)
        return np.concatenate([rep_a, local_thickness, local_camber, [le_proxy]])

    # -------------------------------------------------------------------------
    # Quantitative Contour Distance Metrics (Directives 13, 36)
    # -------------------------------------------------------------------------

    @staticmethod
    def contour_hausdorff_distance(coords_a: np.ndarray, coords_b: np.ndarray) -> float:
        """
        Computes directed Hausdorff distance between two normalized coordinate contours.
        dH(A, B) = max( sup_{x in A} inf_{y in B} ||x - y||, sup_{y in B} inf_{x in A} ||x - y|| )
        """
        # Distance from each point in A to nearest in B
        d_a_to_b = np.min(np.linalg.norm(coords_a[:, None, :] - coords_b[None, :, :], axis=2), axis=1)
        d_b_to_a = np.min(np.linalg.norm(coords_b[:, None, :] - coords_a[None, :, :], axis=2), axis=1)
        return float(max(np.max(d_a_to_b), np.max(d_b_to_a)))

    @staticmethod
    def mean_euclidean_contour_distance(coords_a: np.ndarray, coords_b: np.ndarray) -> float:
        """
        Pointwise mean Euclidean distance between resampled contours of equal length.
        """
        if len(coords_a) != len(coords_b):
            min_len = min(len(coords_a), len(coords_b))
            coords_a = coords_a[:min_len]
            coords_b = coords_b[:min_len]
        return float(np.mean(np.linalg.norm(coords_a - coords_b, axis=1)))

    @staticmethod
    def parameter_mahalanobis_distance(
        sample_params: np.ndarray,
        train_mean: np.ndarray,
        inv_cov: np.ndarray
    ) -> float:
        """
        Mahalanobis distance in parameter space.
        """
        diff = sample_params - train_mean
        d_sq = float(np.dot(np.dot(diff, inv_cov), diff))
        return float(np.sqrt(max(0.0, d_sq)))

    # -------------------------------------------------------------------------
    # Analytical NACA Generator for Benchmark Cases
    # -------------------------------------------------------------------------

    def generate_analytical_naca(self, code: str, n_points: int = 100) -> Tuple[np.ndarray, GeometryProfile]:
        """
        Generates 4-digit or 5-digit analytical NACA coordinates.
        Supports: 0012, 0009, 0006, 2412, 4412, 0018, 23012, 6409, 4415.
        """
        code = code.upper().replace("NACA", "").strip()
        beta = np.linspace(0.0, np.pi, n_points)
        x = 0.5 * (1.0 - np.cos(beta))  # Half-cosine spacing

        if len(code) == 4:
            m = float(code[0]) / 100.0
            p = float(code[1]) / 10.0
            t = float(code[2:]) / 100.0

            # Thickness distribution
            yt = 5.0 * t * (
                0.2969 * np.sqrt(np.maximum(x, 1e-9))
                - 0.1260 * x
                - 0.3516 * (x ** 2)
                + 0.2843 * (x ** 3)
                - 0.1015 * (x ** 4)  # closed trailing edge
            )

            # Camber line
            yc = np.zeros_like(x)
            dyc_dx = np.zeros_like(x)
            if p > 0:
                idx1 = x < p
                idx2 = x >= p
                yc[idx1] = (m / (p ** 2)) * (2.0 * p * x[idx1] - x[idx1] ** 2)
                dyc_dx[idx1] = (2.0 * m / (p ** 2)) * (p - x[idx1])
                yc[idx2] = (m / ((1.0 - p) ** 2)) * ((1.0 - 2.0 * p) + 2.0 * p * x[idx2] - x[idx2] ** 2)
                dyc_dx[idx2] = (2.0 * m / ((1.0 - p) ** 2)) * (p - x[idx2])

            theta = np.arctan(dyc_dx)
            xu = x - yt * np.sin(theta)
            yu = yc + yt * np.cos(theta)
            xl = x + yt * np.sin(theta)
            yl = yc - yt * np.cos(theta)

            # Assemble contour: TE upper -> LE -> TE lower
            upper = np.column_stack([xu[::-1], yu[::-1]])
            lower = np.column_stack([xl[1:], yl[1:]])
            contour = np.vstack([upper, lower])
            return self.process_coordinates(contour, f"NACA {code}")

        elif len(code) == 5:
            # Analytical NACA 23012 standard profile
            t = float(code[3:]) / 100.0
            yt = 5.0 * t * (
                0.2969 * np.sqrt(np.maximum(x, 1e-9))
                - 0.1260 * x
                - 0.3516 * (x ** 2)
                + 0.2843 * (x ** 3)
                - 0.1015 * (x ** 4)
            )
            # NACA 230 standard reflex camber: m=0.15, k1=15.957
            r = 0.2025
            k1 = 15.957
            yc = np.zeros_like(x)
            dyc_dx = np.zeros_like(x)
            idx1 = x < r
            idx2 = x >= r
            yc[idx1] = (k1 / 6.0) * (x[idx1] ** 3 - 3.0 * r * (x[idx1] ** 2) + (r ** 2) * (3.0 - r) * x[idx1])
            dyc_dx[idx1] = (k1 / 6.0) * (3.0 * (x[idx1] ** 2) - 6.0 * r * x[idx1] + (r ** 2) * (3.0 - r))
            yc[idx2] = (k1 * (r ** 3) / 6.0) * (1.0 - x[idx2])
            dyc_dx[idx2] = - (k1 * (r ** 3) / 6.0)

            theta = np.arctan(dyc_dx)
            xu = x - yt * np.sin(theta)
            yu = yc + yt * np.cos(theta)
            xl = x + yt * np.sin(theta)
            yl = yc - yt * np.cos(theta)

            upper = np.column_stack([xu[::-1], yu[::-1]])
            lower = np.column_stack([xl[1:], yl[1:]])
            contour = np.vstack([upper, lower])
            return self.process_coordinates(contour, f"NACA {code}")

        else:
            # Default symmetric 0012 fallback
            return self.generate_analytical_naca("0012", n_points)
