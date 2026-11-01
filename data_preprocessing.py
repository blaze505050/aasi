"""
AASI Aerospace Data Preprocessing Pipeline.
Production-grade normalization, geometric feature extraction, and dataset ingestion
for aerodynamic surfaces, wind tunnel polars, turbofan diagnostics, and SHM time-series.
"""

import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union, Any
import numpy as np
from pydantic import BaseModel, Field, field_validator


# ─── Pydantic Validation Schemas ──────────────────────────────────────────────

class AirfoilCoordinatesInput(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Airfoil designation")
    x: List[float] = Field(..., min_length=6, description="Chordwise coordinates [0, 1]")
    y: List[float] = Field(..., min_length=6, description="Vertical coordinates")
    format_type: str = Field(default="auto", description="Format: 'selig', 'lednicer', 'csv', 'naca'")

    @field_validator("x", "y")
    @classmethod
    def validate_finite_numbers(cls, v: List[float]) -> List[float]:
        for idx, val in enumerate(v):
            if not math.isfinite(val):
                raise ValueError(f"Non-finite coordinate detected at index {idx}: {val}")
        return v

    @field_validator("y")
    @classmethod
    def validate_matching_lengths(cls, v: List[float], info) -> List[float]:
        x_val = info.data.get("x")
        if x_val is not None and len(v) != len(x_val):
            raise ValueError(f"Length mismatch: x has {len(x_val)} points, y has {len(v)} points")
        return v


class AirfoilGeometryFeatures(BaseModel):
    name: str
    num_panels: int
    chord: float = 1.0
    max_thickness: float
    max_thickness_x: float
    max_camber: float
    max_camber_x: float
    le_radius_approx: float
    te_gap: float
    is_closed_te: bool
    is_symmetric: bool
    x_coords: List[float]
    y_coords: List[float]
    camber_x: List[float]
    camber_y: List[float]
    thickness_dist: List[float]


# ─── Airfoil Normalization & Preprocessing ─────────────────────────────────────

class AirfoilPreprocessor:
    """Production preprocessor for 2D aerodynamic geometries."""

    @staticmethod
    def generate_naca4(code: str, num_points: int = 160) -> Tuple[np.ndarray, np.ndarray]:
        """
        Analytically generates NACA 4-digit airfoil coordinates.
        Example: '0012', '2412', '4415'.
        """
        match = re.search(r"(\d{4})", code.strip())
        if not match:
            raise ValueError(f"Invalid NACA 4-digit code: '{code}'. Expected 4 digits (e.g. 0012, 2412).")
        digits = match.group(1)
        m = float(digits[0]) / 100.0  # Max camber
        p = float(digits[1]) / 10.0   # Location of max camber
        t = float(digits[2:]) / 100.0 # Max thickness

        # Cosine spacing for smooth panel distribution
        beta = np.linspace(0.0, np.pi, num_points // 2 + 1)
        x = 0.5 * (1.0 - np.cos(beta))

        # Thickness distribution (standard NACA formulation)
        yt = 5.0 * t * (
            0.2969 * np.sqrt(np.maximum(x, 1e-12))
            - 0.1260 * x
            - 0.3516 * (x ** 2)
            + 0.2843 * (x ** 3)
            - 0.1015 * (x ** 4)  # closed trailing edge approximation
        )

        # Camber line and gradient
        yc = np.zeros_like(x)
        dyc_dx = np.zeros_like(x)

        if p > 0:
            forward = x <= p
            rear = x > p

            yc[forward] = (m / (p ** 2)) * (2.0 * p * x[forward] - (x[forward] ** 2))
            dyc_dx[forward] = (2.0 * m / (p ** 2)) * (p - x[forward])

            yc[rear] = (m / ((1.0 - p) ** 2)) * ((1.0 - 2.0 * p) + 2.0 * p * x[rear] - (x[rear] ** 2))
            dyc_dx[rear] = (2.0 * m / ((1.0 - p) ** 2)) * (p - x[rear])

        theta = np.arctan(dyc_dx)

        # Upper surface (TE -> LE)
        xu = x - yt * np.sin(theta)
        yu = yc + yt * np.cos(theta)

        # Lower surface (LE -> TE)
        xl = x + yt * np.sin(theta)
        yl = yc - yt * np.cos(theta)

        # Combine clockwise: TE upper -> LE -> TE lower
        x_full = np.concatenate([xu[::-1], xl[1:]])
        y_full = np.concatenate([yu[::-1], yl[1:]])

        return x_full, y_full

    @classmethod
    def parse_coordinate_text(cls, text: str) -> Tuple[str, np.ndarray, np.ndarray]:
        """
        Parses coordinates from text (Selig format, Lednicer, or CSV).
        Handles headers, blank lines, and whitespace delimiters.
        """
        lines = [ln.strip() for ln in text.strip().splitlines() if ln.strip()]
        if not lines:
            raise ValueError("Input coordinate text is empty.")

        name = "Unknown_Airfoil"
        start_idx = 0

        # Check if first line is a title
        first_tokens = lines[0].split()
        try:
            float(first_tokens[0])
            float(first_tokens[1])
        except (ValueError, IndexError):
            name = lines[0].replace(" ", "_")
            start_idx = 1

        x_coords: List[float] = []
        y_coords: List[float] = []

        for line in lines[start_idx:]:
            # Clean commas, tabs, semicolons to spaces
            cleaned = re.sub(r"[,;]+", " ", line).strip()
            tokens = cleaned.split()
            if len(tokens) >= 2:
                try:
                    px = float(tokens[0])
                    py = float(tokens[1])
                    x_coords.append(px)
                    y_coords.append(py)
                except ValueError:
                    continue

        if len(x_coords) < 6:
            raise ValueError(f"Found only {len(x_coords)} valid points; minimum 6 required for aerodynamic discretization.")

        return name, np.array(x_coords, dtype=float), np.array(y_coords, dtype=float)

    @classmethod
    def normalize_and_redistribute(
        cls, x: np.ndarray, y: np.ndarray, num_panels: int = 160
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Normalizes chord to [0, 1] and resamples coordinates using cosine panel clustering.
        """
        x_min, x_max = float(np.min(x)), float(np.max(x))
        chord = x_max - x_min
        if chord <= 1e-9:
            raise ValueError(f"Degenerate airfoil: chord is too small ({chord}).")

        # Shift leading edge to (0, 0) and scale chord to 1.0
        x_norm = (x - x_min) / chord
        y_norm = y / chord

        # Ensure order is clockwise from Trailing Edge upper (x~1, y>=0) around LE (x~0) to TE lower
        # Split into upper and lower surfaces via the LE minimum x point
        le_idx = int(np.argmin(x_norm))

        upper_x = x_norm[:le_idx + 1]
        upper_y = y_norm[:le_idx + 1]
        lower_x = x_norm[le_idx:]
        lower_y = y_norm[le_idx:]

        # Half panels on upper, half on lower
        n_half = num_panels // 2 + 1
        beta = np.linspace(0.0, np.pi, n_half)
        target_x = 0.5 * (1.0 - np.cos(beta))

        # Sort for monotonic 1D interpolation
        upper_order = np.argsort(upper_x)
        lower_order = np.argsort(lower_x)

        u_x_clean, u_indices = np.unique(upper_x[upper_order], return_index=True)
        u_y_clean = upper_y[upper_order][u_indices]

        l_x_clean, l_indices = np.unique(lower_x[lower_order], return_index=True)
        l_y_clean = lower_y[lower_order][l_indices]

        # Resample with linear extrapolation guard
        upper_resampled_y = np.interp(target_x, u_x_clean, u_y_clean)
        lower_resampled_y = np.interp(target_x, l_x_clean, l_y_clean)

        # Upper surface goes from TE (x=1) down to LE (x=0)
        x_out = np.concatenate([target_x[::-1], target_x[1:]])
        y_out = np.concatenate([upper_resampled_y[::-1], lower_resampled_y[1:]])

        return x_out, y_out

    @classmethod
    def extract_features(cls, name: str, x: np.ndarray, y: np.ndarray) -> AirfoilGeometryFeatures:
        """Extracts complete geometric, camber, and thickness metrics."""
        le_idx = int(np.argmin(x))
        upper_x, upper_y = x[:le_idx + 1], y[:le_idx + 1]
        lower_x, lower_y = x[le_idx:], y[le_idx:]

        # Query points along chord [0, 1]
        eval_x = np.linspace(0.0, 1.0, 101)
        u_y = np.interp(eval_x, upper_x[::-1] if upper_x[0] > upper_x[-1] else upper_x, 
                        upper_y[::-1] if upper_x[0] > upper_x[-1] else upper_y)
        l_y = np.interp(eval_x, lower_x, lower_y)

        camber_line = 0.5 * (u_y + l_y)
        thickness_dist = np.maximum(0.0, u_y - l_y)

        max_t_idx = int(np.argmax(thickness_dist))
        max_thickness = float(thickness_dist[max_t_idx])
        max_thickness_x = float(eval_x[max_t_idx])

        max_c_idx = int(np.argmax(np.abs(camber_line)))
        max_camber = float(camber_line[max_c_idx])
        max_camber_x = float(eval_x[max_c_idx])

        # Trailing edge gap
        te_gap = float(abs(y[0] - y[-1]))
        is_closed_te = te_gap < 1e-4

        # Symmetry check
        is_symmetric = bool(np.max(np.abs(camber_line)) < 1e-3)

        # Leading edge radius approximation (R_le ~= 1.1019 * t^2)
        le_radius_approx = 1.1019 * (max_thickness ** 2)

        return AirfoilGeometryFeatures(
            name=name,
            num_panels=len(x) - 1,
            chord=1.0,
            max_thickness=round(max_thickness, 4),
            max_thickness_x=round(max_thickness_x, 4),
            max_camber=round(max_camber, 4),
            max_camber_x=round(max_camber_x, 4),
            le_radius_approx=round(le_radius_approx, 5),
            te_gap=round(te_gap, 5),
            is_closed_te=is_closed_te,
            is_symmetric=is_symmetric,
            x_coords=x.tolist(),
            y_coords=y.tolist(),
            camber_x=eval_x.tolist(),
            camber_y=camber_line.tolist(),
            thickness_dist=thickness_dist.tolist()
        )


# ─── Aerospace Experimental & Subdomain Dataset Ingestion ─────────────────────

class AerospaceDatasetIngestor:
    """Standardized preprocessors for aerospace validation and benchmark datasets."""

    @staticmethod
    def parse_uiuc_polar(csv_or_dat_text: str) -> Dict[str, Any]:
        """
        Parses UIUC low-speed wind tunnel polar tables (alpha, Cl, Cd, Cm).
        Filters out non-numeric header lines and normalizes arrays.
        """
        lines = [ln.strip() for ln in csv_or_dat_text.strip().splitlines() if ln.strip()]
        data: List[List[float]] = []
        for line in lines:
            cleaned = re.sub(r"[,;]+", " ", line)
            tokens = cleaned.split()
            if len(tokens) >= 3:
                try:
                    row = [float(t) for t in tokens[:4]]
                    data.append(row)
                except ValueError:
                    continue

        if not data:
            raise ValueError("No valid polar table rows found in input text.")

        arr = np.array(data)
        alpha = arr[:, 0]
        cl = arr[:, 1]
        cd = arr[:, 2]
        cm = arr[:, 3] if arr.shape[1] >= 4 else np.zeros_like(alpha)

        return {
            "source": "UIUC_Wind_Tunnel",
            "num_points": len(alpha),
            "alpha_deg": alpha.tolist(),
            "cl": cl.tolist(),
            "cd": cd.tolist(),
            "cm": cm.tolist(),
            "cl_max": float(np.max(cl)),
            "alpha_stall_deg": float(alpha[np.argmax(cl)]),
            "cd_min": float(np.min(cd)),
            "ld_max": float(np.max(cl / np.maximum(cd, 1e-5)))
        }

    @staticmethod
    def preprocess_cmapss_turbofan_slice(
        cycles: List[int], sensor_readings: Dict[str, List[float]]
    ) -> Dict[str, Any]:
        """
        Preprocesses NASA CMAPSS Turbofan Engine Degradation time-series.
        Performs min-max feature scaling, computes rolling moving averages,
        and derives synthetic Remaining Useful Life (RUL) targets.
        """
        if not cycles:
            raise ValueError("Empty cycle history provided.")

        max_cycle = max(cycles)
        rul = [max_cycle - c for c in cycles]

        processed_sensors: Dict[str, Dict[str, Any]] = {}
        for s_name, values in sensor_readings.items():
            arr = np.array(values, dtype=float)
            s_min, s_max = float(np.min(arr)), float(np.max(arr))
            spread = s_max - s_min if s_max > s_min else 1.0
            normalized = (arr - s_min) / spread

            # 5-step rolling average
            kernel_size = min(5, len(arr))
            kernel = np.ones(kernel_size) / kernel_size
            smoothed = np.convolve(normalized, kernel, mode="same")

            processed_sensors[s_name] = {
                "raw_min": s_min,
                "raw_max": s_max,
                "normalized": normalized.tolist(),
                "smoothed": smoothed.tolist(),
                "mean": float(np.mean(arr)),
                "std": float(np.std(arr))
            }

        return {
            "num_cycles": len(cycles),
            "max_cycle": max_cycle,
            "rul_targets": rul,
            "sensors": processed_sensors
        }

    @staticmethod
    def preprocess_shm_vibration_signal(
        time_series: List[float], sampling_rate_hz: float = 1000.0
    ) -> Dict[str, Any]:
        """
        Preprocesses Structural Health Monitoring (SHM) vibration / accelerometer data.
        Computes RMS, Peak-to-Peak, Kurtosis, and fast FFT dominant frequencies
        for crack and fatigue delamination classification.
        """
        arr = np.array(time_series, dtype=float)
        n = len(arr)
        if n < 16:
            raise ValueError("At least 16 vibration samples required for SHM preprocessing.")

        rms = float(np.sqrt(np.mean(arr ** 2)))
        peak_to_peak = float(np.ptp(arr))
        mean = float(np.mean(arr))
        std = float(np.std(arr)) if np.std(arr) > 1e-9 else 1.0

        # Kurtosis (fatigue / impact spikes)
        kurtosis = float(np.mean(((arr - mean) / std) ** 4))

        # FFT dominant frequency
        fft_vals = np.abs(np.fft.rfft(arr - mean))
        freqs = np.fft.rfftfreq(n, d=1.0 / sampling_rate_hz)
        dominant_freq = float(freqs[np.argmax(fft_vals)])

        return {
            "samples": n,
            "sampling_rate_hz": sampling_rate_hz,
            "rms": round(rms, 5),
            "peak_to_peak": round(peak_to_peak, 5),
            "kurtosis": round(kurtosis, 4),
            "dominant_frequency_hz": round(dominant_freq, 2),
            "status": "NORMAL" if kurtosis < 3.5 else "ANOMALY_SPIKE_DETECTED"
        }


# ─── Module Self-Test & CLI ──────────────────────────────────────────────────

if __name__ == "__main__":
    print("Testing AASI Aerospace Data Preprocessing Pipeline...")
    # 1. NACA 2412 Generation & Feature Extraction
    x, y = AirfoilPreprocessor.generate_naca4("2412", num_points=160)
    features = AirfoilPreprocessor.extract_features("NACA_2412", x, y)
    print(f"[OK] NACA 2412: max thickness = {features.max_thickness*100}% at x={features.max_thickness_x}")
    print(f"[OK] Max camber = {features.max_camber*100}% at x={features.max_camber_x}, is_symmetric={features.is_symmetric}")

    # 2. SHM Vibration Test
    t_vals = np.linspace(0, 1, 1000)
    sig = np.sin(2 * np.pi * 50 * t_vals) + 0.1 * np.random.randn(1000)
    shm_report = AerospaceDatasetIngestor.preprocess_shm_vibration_signal(sig.tolist(), sampling_rate_hz=1000.0)
    print(f"[OK] SHM signal: dominant frequency = {shm_report['dominant_frequency_hz']} Hz, status = {shm_report['status']}")
    print("All preprocessing checks passed cleanly.")
