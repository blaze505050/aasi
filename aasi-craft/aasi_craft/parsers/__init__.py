"""
Deterministic Aerospace Parsers for AASI-Craft.
Extracts ground-truth evidence from OpenFOAM, CCSDS telemetry, NavIC RINEX, and wind tunnel polars.
"""

from .openfoam_parser import OpenFoamCaseParser
from .telemetry_parser import CcsdsTelemetryParser, NavicRinexParser
from .polar_parser import AirfoilPolarParser

__all__ = [
    "OpenFoamCaseParser",
    "CcsdsTelemetryParser",
    "NavicRinexParser",
    "AirfoilPolarParser",
]

