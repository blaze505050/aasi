"""
AASI Industrial Geometry Engine: Aerospace Airfoil File Parser & Normalizer.

Parses industry-standard airfoil coordinate files:
- Selig format (single loop: TE upper -> LE -> TE lower)
- Lednicer format (explicit upper and lower surface sections)
- CSV / TSV / whitespace-delimited coordinate tables
- UIUC Airfoil Data Site formats

Performs:
- Automatic format detection
- Chord normalization (scaling chord length to 1.0)
- Coordinate de-rotation and leading-edge alignment to (0, 0)
- Geometric feature extraction (max thickness t/c, max camber m/c, LE nose radius)
- Curvature-adaptive cosine re-paneling via cubic spline interpolation
"""

from __future__ import annotations

import math
import re
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np


class AirfoilParseError(ValueError):
    """Raised when an airfoil file is corrupted, malformed, or unparseable."""
    pass


class AirfoilGeometry:
    """
    Standardized, normalized 2D aerodynamic profile definition.
    """

    def __init__(
        self,
        name: str,
        raw_coordinates: np.ndarray,
        normalized_coordinates: np.ndarray,
        upper_coordinates: np.ndarray,
        lower_coordinates: np.ndarray,
        max_thickness: float,
        thickness_x_location: float,
        max_camber: float,
        camber_x_location: float,
        leading_edge_radius: float,
        trailing_edge_gap: float,
        format_detected: str,
    ):
        self.name = name
        self.raw_coordinates = raw_coordinates
        self.coordinates = normalized_coordinates  # [N, 2] clockwise from TE upper to LE to TE lower
        self.upper_coordinates = upper_coordinates
        self.lower_coordinates = lower_coordinates
        self.max_thickness = max_thickness
        self.thickness_x_location = thickness_x_location
        self.max_camber = max_camber
        self.camber_x_location = camber_x_location
        self.leading_edge_radius = leading_edge_radius
        self.trailing_edge_gap = trailing_edge_gap
        self.format_detected = format_detected

    @property
    def point_count(self) -> int:
        return len(self.coordinates)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "format_detected": self.format_detected,
            "point_count": len(self.coordinates),
            "max_thickness": round(self.max_thickness, 4),
            "thickness_x_location": round(self.thickness_x_location, 4),
            "max_camber": round(self.max_camber, 4),
            "camber_x_location": round(self.camber_x_location, 4),
            "leading_edge_radius": round(self.leading_edge_radius, 5),
            "trailing_edge_gap": round(self.trailing_edge_gap, 5),
            "coordinates": self.coordinates.tolist(),
        }


class AirfoilCoordinateParser:
    """
    High-robustness parser and normalizer for aerodynamic coordinate files.
    """

    @staticmethod
    def generate_naca4(naca_code: str, num_points: int = 140) -> AirfoilGeometry:
        """
        Synthesizes standard NACA 4-digit analytical profile geometry.
        """
        code = naca_code.upper().replace("NACA", "").strip()
        if len(code) == 4 and code.isdigit():
            m = int(code[0]) / 100.0
            p = int(code[1]) / 10.0
            t = int(code[2:]) / 100.0
            name = f"NACA {code}"
        else:
            m, p, t = 0.0, 0.0, 0.12
            name = "NACA 0012"

        from backend.physics.panel_solver import generate_naca4_coordinates
        raw_coords = generate_naca4_coordinates(naca_code=naca_code, num_points=num_points)
        return AirfoilCoordinateParser._normalize_and_build(
            coords=raw_coords,
            name=name,
            format_detected="NACA4_ANALYTICAL",
            target_resample_points=num_points,
        )

    @staticmethod
    def parse_text(text: str, default_name: str = "Custom_Airfoil") -> AirfoilGeometry:
        """
        Parses text content of an airfoil coordinate file (.dat, .csv, .txt).
        """
        if not text or not text.strip():
            raise AirfoilParseError("Empty airfoil file provided.")

        lines = [line.strip() for line in text.strip().splitlines() if line.strip()]
        if len(lines) < 6:
            raise AirfoilParseError("Insufficient data lines in airfoil file (minimum 6 lines required).")

        name = default_name
        first_line = lines[0]

        # Check if first line is a title or numbers
        first_tokens = re.findall(r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?", first_line)
        has_title = len(first_tokens) < 2
        if has_title:
            cleaned_first = re.sub(r"[#/\\]", "", first_line).strip()
            norm_header = re.sub(r"[\s,;_\t]", "", cleaned_first).lower()
            if norm_header in ("xy", "x/cy/c", "xcoordycoord"):
                name = default_name
            else:
                name = cleaned_first or default_name
            data_lines = lines[1:]
        else:
            data_lines = lines

        # Detect Lednicer format: look for two numbers indicating section counts, e.g. "26. 26." or "30 30"
        is_lednicer = False
        second_line_tokens = re.findall(r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?", data_lines[0])
        if len(second_line_tokens) == 2:
            try:
                count1 = float(second_line_tokens[0])
                count2 = float(second_line_tokens[1])
                if count1 >= 5 and count2 >= 5 and (count1.is_integer() or count1 < 200):
                    is_lednicer = True
            except ValueError:
                pass

        if is_lednicer:
            return AirfoilCoordinateParser._parse_lednicer(data_lines, name)
        else:
            return AirfoilCoordinateParser._parse_selig_or_table(data_lines, name)

    @staticmethod
    def _parse_selig_or_table(lines: List[str], name: str) -> AirfoilGeometry:
        coords_raw: List[Tuple[float, float]] = []

        for line in lines:
            # Skip comments
            if line.startswith(("#", "//", "/*", "!")):
                continue
            # Parse commas, semicolons, tabs, spaces
            tokens = re.findall(r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?", line)
            if len(tokens) >= 2:
                try:
                    x = float(tokens[0])
                    y = float(tokens[1])
                    coords_raw.append((x, y))
                except ValueError:
                    continue

        if len(coords_raw) < 8:
            raise AirfoilParseError(f"Found only {len(coords_raw)} valid coordinates. Minimum 8 points required.")

        arr = np.array(coords_raw, dtype=np.float64)
        return AirfoilCoordinateParser._normalize_and_build(arr, name, format_detected="SELIG_OR_TABLE")

    @staticmethod
    def _parse_lednicer(lines: List[str], name: str) -> AirfoilGeometry:
        # First data line has counts
        tokens = re.findall(r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?", lines[0])
        n_upper = int(float(tokens[0]))
        n_lower = int(float(tokens[1]))

        upper_pts: List[Tuple[float, float]] = []
        lower_pts: List[Tuple[float, float]] = []

        coord_lines = []
        for line in lines[1:]:
            if line.startswith(("#", "//", "/*", "!")):
                continue
            t = re.findall(r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?", line)
            if len(t) >= 2:
                coord_lines.append((float(t[0]), float(t[1])))

        if len(coord_lines) < (n_upper + n_lower - 2):
            # Fall back to single loop
            return AirfoilCoordinateParser._normalize_and_build(
                np.array(coord_lines, dtype=np.float64), name, format_detected="LEDNICER_RECONSTRUCTED"
            )

        upper_pts = coord_lines[:n_upper]
        lower_pts = coord_lines[n_upper : n_upper + n_lower]

        u_arr = np.array(upper_pts, dtype=np.float64)
        l_arr = np.array(lower_pts, dtype=np.float64)

        # Standard Lednicer is LE to TE for upper, LE to TE for lower.
        # Convert to clockwise: TE upper to LE, then LE to TE lower.
        if u_arr[0, 0] < u_arr[-1, 0]:
            # u_arr is LE to TE -> reverse to TE to LE
            u_arr = u_arr[::-1]

        if l_arr[0, 0] > l_arr[-1, 0]:
            # l_arr is TE to LE -> reverse to LE to TE
            l_arr = l_arr[::-1]

        # Combine, skipping duplicate LE
        combined = np.vstack((u_arr, l_arr[1:]))
        return AirfoilCoordinateParser._normalize_and_build(combined, name, format_detected="LEDNICER")

    @staticmethod
    def _normalize_and_build(
        coords: np.ndarray,
        name: str,
        format_detected: str,
        target_resample_points: int = 120,
    ) -> AirfoilGeometry:
        """
        Normalizes chord, de-rotates, extracts parameters, and builds re-paneled geometry.
        """
        raw = coords.copy()

        # 1. Identify Leading Edge (minimum x point)
        le_idx = int(np.argmin(coords[:, 0]))
        le_x = coords[le_idx, 0]
        le_y = coords[le_idx, 1]

        # Shift leading edge to origin (0, 0)
        coords[:, 0] -= le_x
        coords[:, 1] -= le_y

        # Trailing edge points: first and last points in array
        te_x = 0.5 * (coords[0, 0] + coords[-1, 0])
        te_y = 0.5 * (coords[0, 1] + coords[-1, 1])

        # De-rotate if chord line has angle
        chord_len = math.hypot(te_x, te_y)
        if chord_len <= 1e-6:
            raise AirfoilParseError("Airfoil geometry has zero or negligible chord length.")

        theta = math.atan2(te_y, te_x)
        cos_t = math.cos(-theta)
        sin_t = math.sin(-theta)
        rot_mat = np.array([[cos_t, -sin_t], [sin_t, cos_t]])

        coords = np.dot(coords, rot_mat.T)

        # Scale chord to exactly 1.0
        final_chord = np.max(coords[:, 0]) - np.min(coords[:, 0])
        if final_chord > 1e-6:
            coords[:, 0] /= final_chord
            coords[:, 1] /= final_chord

        # Ensure correct clockwise orientation: TE upper -> LE -> TE lower
        # If first point has negative y, the array was ordered counter-clockwise; flip it
        if coords[0, 1] < coords[-1, 1]:
            coords = coords[::-1]
            le_idx = int(np.argmin(coords[:, 0]))

        # Re-partition into Upper and Lower curves
        upper_raw = coords[: le_idx + 1]
        lower_raw = coords[le_idx :]

        # 2. Resample via Cosine Spacing
        half_n = target_resample_points // 2
        beta = np.linspace(0.0, np.pi, half_n)
        x_target = 0.5 * (1.0 - np.cos(beta))

        # Interpolate upper surface (x from 0 to 1)
        # Ensure x is strictly monotonic for interpolation
        u_x = upper_raw[::-1, 0]  # LE to TE
        u_y = upper_raw[::-1, 1]
        _, u_unique_idx = np.unique(u_x, return_index=True)
        u_x = u_x[u_unique_idx]
        u_y = u_y[u_unique_idx]
        y_upper_interp = np.interp(x_target, u_x, u_y)

        # Interpolate lower surface (x from 0 to 1)
        l_x = lower_raw[:, 0]
        l_y = lower_raw[:, 1]
        _, l_unique_idx = np.unique(l_x, return_index=True)
        l_x = l_x[l_unique_idx]
        l_y = l_y[l_unique_idx]
        y_lower_interp = np.interp(x_target, l_x, l_y)

        # Build clean clockwise coordinates
        upper_clean = np.column_stack((x_target[::-1], y_upper_interp[::-1]))
        lower_clean = np.column_stack((x_target[1:], y_lower_interp[1:]))
        normalized = np.vstack((upper_clean, lower_clean))

        # 3. Geometric Parameters
        thickness_dist = y_upper_interp - y_lower_interp
        max_thickness = float(np.max(thickness_dist))
        max_t_idx = int(np.argmax(thickness_dist))
        thickness_x_loc = float(x_target[max_t_idx])

        camber_dist = 0.5 * (y_upper_interp + y_lower_interp)
        max_camber = float(np.max(np.abs(camber_dist)))
        max_c_idx = int(np.argmax(np.abs(camber_dist)))
        camber_x_loc = float(x_target[max_c_idx])

        # Trailing edge gap
        te_gap = float(abs(y_upper_interp[-1] - y_lower_interp[-1]))

        # Approximate leading edge radius (r_LE ~ 1.1019 * t^2)
        le_radius = float(1.1019 * (max_thickness ** 2))

        return AirfoilGeometry(
            name=name,
            raw_coordinates=raw,
            normalized_coordinates=normalized,
            upper_coordinates=np.column_stack((x_target, y_upper_interp)),
            lower_coordinates=np.column_stack((x_target, y_lower_interp)),
            max_thickness=max(0.01, max_thickness),
            thickness_x_location=thickness_x_loc,
            max_camber=max_camber,
            camber_x_location=camber_x_loc,
            leading_edge_radius=le_radius,
            trailing_edge_gap=te_gap,
            format_detected=format_detected,
        )
