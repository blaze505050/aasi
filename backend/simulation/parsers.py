"""Log and solution parsers for OpenFOAM, SU2, and XFOIL output streams."""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple


class OpenFOAMLogParser:
    """Parses OpenFOAM standard output logs, residual convergence histories, and force coefficients."""

    # Matches linear solver residual line:
    # "smoothSolver:  Solving for Ux, Initial residual = 0.0451, Final residual = 0.00041, No Iterations 5"
    RESIDUAL_PATTERN = re.compile(
        r"(?:smoothSolver|GAMG|PBiCGStab|PCG|PBiCG):\s+Solving for ([A-Za-z0-9_]+),\s+Initial residual = ([0-9.eE+-]+),\s+Final residual = ([0-9.eE+-]+)",
        re.IGNORECASE,
    )

    # Matches forceCoeffs output lines:
    # "forces forces: Cl = 0.8152, Cd = 0.0145, Cm = -0.0028"
    # or "Time = 500: Cl = 0.8152, Cd = 0.0145"
    FORCE_COEFFS_PATTERN = re.compile(
        r"\b(?:Cl|lift)\s*(?:=|\s)\s*(-?[0-9]*\.?[0-9]+(?:[eE][-+]?[0-9]+)?).*?\b(?:Cd|drag)\s*(?:=|\s)\s*(-?[0-9]*\.?[0-9]+(?:[eE][-+]?[0-9]+)?)(?:.*?\b(?:Cm|moment)\s*(?:=|\s)\s*(-?[0-9]*\.?[0-9]+(?:[eE][-+]?[0-9]+)?))?",
        re.IGNORECASE,
    )

    # Alternate OpenFOAM postProcessing tabular lines:
    # "# Time   Cd   Cd(f)   Cd(r)   Cl   Cl(f)   Cl(r)   CmPitch"
    TABLE_PATTERN = re.compile(
        r"^\s*([0-9.]+)\s+([0-9.eE+-]+)\s+[0-9.eE+-]+\s+[0-9.eE+-]+\s+([0-9.eE+-]+)\s+[0-9.eE+-]+\s+[0-9.eE+-]+\s+([0-9.eE+-]+)",
        re.MULTILINE,
    )

    def parse_residuals(self, log_content: str) -> Dict[str, float]:
        """Extract latest initial residuals for all solved fields (p, Ux, Uy, k, omega, nuTilda)."""
        latest_residuals: Dict[str, float] = {}
        for match in self.RESIDUAL_PATTERN.finditer(log_content):
            var_name = match.group(1)
            initial_res = float(match.group(2))
            latest_residuals[var_name] = initial_res
        return latest_residuals

    def parse_force_coefficients(self, log_content: str) -> Tuple[Optional[float], Optional[float], Optional[float]]:
        """Extract final Cl, Cd, and Cm from OpenFOAM log or function object text."""
        cl, cd, cm = None, None, None

        # 1. Search for combined or individual Cl, Cd, Cm in text
        cl_match = re.findall(r"\b(?:Cl|lift)\s*=\s*(-?[0-9]*\.?[0-9]+(?:[eE][-+]?[0-9]+)?)", log_content, re.IGNORECASE)
        cd_match = re.findall(r"\b(?:Cd|drag)\s*=\s*(-?[0-9]*\.?[0-9]+(?:[eE][-+]?[0-9]+)?)", log_content, re.IGNORECASE)
        cm_match = re.findall(r"\b(?:Cm|moment)\s*=\s*(-?[0-9]*\.?[0-9]+(?:[eE][-+]?[0-9]+)?)", log_content, re.IGNORECASE)

        if cl_match:
            try:
                cl = float(cl_match[-1])
            except ValueError:
                pass
        if cd_match:
            try:
                cd = float(cd_match[-1])
            except ValueError:
                pass
        if cm_match:
            try:
                cm = float(cm_match[-1])
            except ValueError:
                pass

        # 2. Check table format if not found
        if cl is None or cd is None:
            table_matches = list(self.TABLE_PATTERN.finditer(log_content))
            if table_matches:
                last = table_matches[-1]
                cd = float(last.group(2))
                cl = float(last.group(3))
                cm = float(last.group(4))

        return cl, cd, cm

    def check_convergence(
        self,
        residuals: Dict[str, float],
        tolerance: float = 1e-5,
    ) -> bool:
        """Check if all key flow variables have converged below the specified threshold."""
        if not residuals:
            return False
        # Key variables must all be <= tolerance
        return all(res <= tolerance for res in residuals.values())


class SU2LogParser:
    """Parses SU2 convergence history files (history.csv)."""

    def parse_history_csv(self, csv_content: str) -> Dict[str, Any]:
        """Extract final aerodynamic coefficients and residual convergence from SU2 history output."""
        lines = [line.strip() for line in csv_content.splitlines() if line.strip()]
        if len(lines) < 2:
            return {}

        headers = [h.strip().strip('"') for h in lines[0].split(",")]
        last_row = [v.strip().strip('"') for v in lines[-1].split(",")]

        row_dict = dict(zip(headers, last_row))
        parsed = {}
        for k, v in row_dict.items():
            try:
                parsed[k] = float(v)
            except ValueError:
                parsed[k] = v
        return parsed
