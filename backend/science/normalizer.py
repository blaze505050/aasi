"""Engineering query normalization layer for aerodynamics, propulsion, and orbital mechanics."""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple
from .models import FlowRegime, NormalizedConditions
from backend.tools.units import unit_registry


class EngineeringQueryNormalizer:
    """Normalizes natural language engineering inquiries into canonical SI and physical conditions."""

    # Airfoil geometry patterns
    AIRFOIL_PATTERNS = [
        r"\b(NACA\s*[-_]?\s*\d{4,5}[A-Za-z0-9]*)\b",
        r"\b(NACA\s*[-_]?\s*6\d[A-Za-z0-9-]*)\b",
        r"\b(RAE\s*2822)\b",
        r"\b(ONERA\s*M6)\b",
        r"\b(CLARK\s*[-_]?\s*Y)\b",
    ]

    # Target variable keywords
    TARGET_VARIABLES = {
        "CD": ["drag coefficient", "cd", "drag polar", "profile drag", "total drag", "minimum drag"],
        "CL": ["lift coefficient", "cl", "lift curve", "lift slope", "cl_max", "maximum lift"],
        "CM": ["pitching moment", "cm", "moment coefficient", "aerodynamic center"],
        "CP": ["pressure coefficient", "cp", "pressure distribution", "cp_min"],
        "L_D": ["lift to drag", "l/d", "lift-to-drag", "aerodynamic efficiency"],
        "ORBITAL_VELOCITY": ["orbital velocity", "orbital speed", "circular velocity"],
        "ORBITAL_PERIOD": ["orbital period", "period of orbit", "time to complete an orbit"],
        "ESCAPE_VELOCITY": ["escape velocity", "escape speed"],
        "DELTA_V": ["delta-v", "deltav", "delta v", "dv", "velocity increment"],
        "PROPELLANT_MASS": ["propellant mass", "fuel mass", "mass of fuel", "propellant required"],
    }

    def normalize(self, query: str) -> NormalizedConditions:
        """Parse natural language query and extract structured physical conditions."""
        q_clean = query.strip()
        conditions = NormalizedConditions(raw_query=q_clean)

        # 1. Geometry Normalization
        geo = self._extract_geometry(q_clean)
        if geo:
            conditions.geometry = geo

        # 2. Flow Conditions Extraction
        # Mach
        mach = self._extract_mach(q_clean)
        if mach is not None:
            conditions.mach = mach
            conditions.flow_regime = self._classify_flow_regime(mach)

        # Reynolds number
        reynolds = self._extract_reynolds(q_clean)
        if reynolds is not None:
            conditions.reynolds = reynolds

        # Angle of Attack
        aoa = self._extract_aoa(q_clean)
        if aoa is not None:
            conditions.aoa_deg = aoa

        # 3. Secondary Thermodynamics / Atmospheric Parameters
        params = self._extract_secondary_parameters(q_clean)
        conditions.parameters.update(params)

        # 4. Target Variables
        targets = self._extract_target_variables(q_clean)
        conditions.requested_outputs = targets

        # 5. Domain Classification
        conditions.domain = self._classify_domain(q_clean, conditions)

        # 6. Physical Completeness Audit
        missing = self._detect_missing_conditions(conditions)
        conditions.missing_critical_conditions = missing

        return conditions

    def _extract_geometry(self, text: str) -> Optional[str]:
        """Extract and normalize airfoil / body geometry."""
        for pattern in self.AIRFOIL_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                raw = match.group(1).upper()
                # Normalize NACA format: "NACA-0012", "NACA0012" -> "NACA 0012"
                if "NACA" in raw:
                    nums = re.sub(r"[^0-9A-Z]", "", raw[4:])
                    return f"NACA {nums}"
                elif "RAE" in raw:
                    return "RAE 2822"
                elif "ONERA" in raw:
                    return "ONERA M6"
                elif "CLARK" in raw:
                    return "Clark-Y"
                return raw
        return None

    def _extract_mach(self, text: str) -> Optional[float]:
        """Extract Mach number from variations (Mach 0.3, M=0.3, M0.3, Mach=0.85)."""
        patterns = [
            r"\b(?:Mach|M)\s*(?:=|is|at|of|\s)?\s*([0-9]*\.?[0-9]+)\b",
            r"\bM([0-9]\.[0-9]+)\b",
        ]
        for pat in patterns:
            match = re.search(pat, text, re.IGNORECASE)
            if match:
                try:
                    val = float(match.group(1))
                    if 0.0 <= val <= 25.0:
                        return val
                except ValueError:
                    pass
        return None

    def _extract_reynolds(self, text: str) -> Optional[float]:
        """Extract Reynolds number from variations (Re 500k, Re=5e5, 500,000 Reynolds, Re=500000)."""
        # Form: Re = 500k or 500k Reynolds
        k_match = re.search(r"\b(?:Reynolds|Re)?\s*(?:number)?\s*(?:=|is|at|of|\s)?\s*([0-9]+(?:\.[0-9]+)?)\s*k\b", text, re.IGNORECASE)
        if k_match:
            try:
                return float(k_match.group(1)) * 1000.0
            except ValueError:
                pass

        # Form: Re = 5e5 or 5.0e6 or 500,000 or 500000
        patterns = [
            r"\b(?:Reynolds|Re)\s*(?:number)?\s*(?:=|is|at|of|\s)?\s*([0-9]+(?:\.[0-9]+)?e[0-9]+)\b",
            r"\b(?:Reynolds|Re)\s*(?:number)?\s*(?:=|is|at|of|\s)?\s*([0-9]{1,3}(?:,[0-9]{3})+)\b",
            r"\b(?:Reynolds|Re)\s*(?:number)?\s*(?:=|is|at|of|\s)?\s*([0-9]{4,10})\b",
            r"\b([0-9]{1,3}(?:,[0-9]{3})+|[0-9]{4,10})\s*(?:Reynolds|Re)\b",
        ]
        for pat in patterns:
            match = re.search(pat, text, re.IGNORECASE)
            if match:
                raw_str = match.group(1).replace(",", "")
                try:
                    val = float(raw_str)
                    if 100.0 <= val <= 1e9:
                        return val
                except ValueError:
                    pass
        return None

    def _extract_aoa(self, text: str) -> Optional[float]:
        """Extract angle of attack (alpha = 8°, AoA 8 deg, 8 degrees, -4 deg)."""
        patterns = [
            r"\b(?:AoA|alpha|angle\s+of\s+attack)\s*(?:=|is|at|of|\s)?\s*(-?[0-9]+(?:\.[0-9]+)?)\s*(?:°|deg|degrees)?\b",
            r"(-?[0-9]+(?:\.[0-9]+)?)\s*(?:°|deg|degrees)\s*(?:AoA|alpha|angle\s+of\s+attack)\b",
            r"\bat\s+(-?[0-9]+(?:\.[0-9]+)?)\s*(?:°|deg|degrees)\b",
            r"\b(-?[0-9]+(?:\.[0-9]+)?)\s*degrees\b",
        ]
        for pat in patterns:
            match = re.search(pat, text, re.IGNORECASE)
            if match:
                try:
                    val = float(match.group(1))
                    if -180.0 <= val <= 180.0:
                        return val
                except ValueError:
                    pass
        return None

    def _extract_secondary_parameters(self, text: str) -> Dict[str, Any]:
        """Extract secondary dimensional physical parameters (altitude, temperature, pressure, velocity, mass)."""
        params: Dict[str, Any] = {}

        # Altitude
        alt_match = re.search(r"\b(?:altitude|alt)\s*(?:=|is|at|of|\s)?\s*([0-9]+(?:\.[0-9]+)?)\s*(km|m|miles|ft)\b", text, re.IGNORECASE)
        if alt_match:
            val = float(alt_match.group(1))
            unit = alt_match.group(2).lower()
            # Convert to canonical km
            if unit == "m":
                val = val / 1000.0
            elif unit == "miles":
                val = val * 1.60934
            elif unit == "ft":
                val = val * 0.0003048
            params["altitude_km"] = val

        # Velocity
        vel_match = re.search(r"\b(?:velocity|speed)\s*(?:=|is|at|of|\s)?\s*([0-9]+(?:\.[0-9]+)?)\s*(m/s|km/s|km/h|knots|mph)\b", text, re.IGNORECASE)
        if vel_match:
            params["velocity_m_s"] = float(vel_match.group(1))

        # Temperature
        temp_match = re.search(r"\b(?:temperature|temp)\s*(?:=|is|at|of|\s)?\s*([0-9]+(?:\.[0-9]+)?)\s*(K|C|F)\b", text, re.IGNORECASE)
        if temp_match:
            params["temperature_k"] = float(temp_match.group(1))

        # Mass
        mass_match = re.search(r"\b(?:mass|weight)\s*(?:=|is|at|of|\s)?\s*([0-9]+(?:\.[0-9]+)?)\s*(kg|tonnes|t|lbs)\b", text, re.IGNORECASE)
        if mass_match:
            params["mass_kg"] = float(mass_match.group(1))

        # Isp
        isp_match = re.search(r"\b(?:Isp|specific\s+impulse)\s*(?:=|is|at|of|\s)?\s*([0-9]+(?:\.[0-9]+)?)\s*(?:s|sec|seconds)?\b", text, re.IGNORECASE)
        if isp_match:
            params["isp_s"] = float(isp_match.group(1))

        return params

    def _extract_target_variables(self, text: str) -> List[str]:
        """Detect what variables the user is asking to calculate or look up."""
        text_lower = text.lower()
        targets: List[str] = []
        for var_name, keywords in self.TARGET_VARIABLES.items():
            if any(kw in text_lower for kw in keywords):
                targets.append(var_name)
        return targets

    def _classify_flow_regime(self, mach: float) -> FlowRegime:
        """Classify flow regime based on Mach number."""
        if mach < 0.3:
            return FlowRegime.INCOMPRESSIBLE
        elif mach < 0.8:
            return FlowRegime.SUBSONIC
        elif mach < 1.2:
            return FlowRegime.TRANSONIC
        elif mach < 5.0:
            return FlowRegime.SUPERSONIC
        else:
            return FlowRegime.HYPERSONIC

    def _classify_domain(self, text: str, cond: NormalizedConditions) -> str:
        """Classify engineering domain."""
        t = text.lower()
        if any(w in t for w in ["orbit", "satellite", "hohmann", "perigee", "apogee", "kepler", "escape velocity"]):
            return "orbital_mechanics"
        elif any(w in t for w in ["rocket", "isp", "thrust", "tsiolkovsky", "propellant", "nozzle"]):
            return "propulsion"
        elif any(w in t for w in ["heat", "temperature", "conduction", "radiation", "thermal"]):
            return "thermal"
        elif any(w in t for w in ["cfd", "mesh", "openfoam", "su2", "rans", "les"]):
            return "cfd"
        elif cond.geometry or cond.aoa_deg is not None or any(v in cond.requested_outputs for v in ["CD", "CL", "CM", "CP", "L_D"]):
            return "aerodynamics"
        return "general_aerospace"

    def _detect_missing_conditions(self, cond: NormalizedConditions) -> List[str]:
        """Detect missing critical conditions for physical determinism."""
        missing: List[str] = []

        # For external aerodynamic force coefficients (CD, CL, CM)
        if any(var in cond.requested_outputs for var in ["CD", "CL", "CM", "L_D"]):
            if not cond.geometry:
                missing.append("geometry (e.g. NACA 0012)")
            if cond.mach is None:
                missing.append("Mach number (e.g. Mach 0.3)")
            if cond.reynolds is None:
                missing.append("Reynolds number (e.g. Re 500,000)")
            if cond.aoa_deg is None:
                missing.append("Angle of attack (e.g. AoA = 8 deg)")

        # For orbital mechanics
        if "ORBITAL_VELOCITY" in cond.requested_outputs or "ORBITAL_PERIOD" in cond.requested_outputs:
            if "altitude_km" not in cond.parameters:
                missing.append("orbital altitude in km")

        return missing
