"""
Dimensional analysis and unit conversion tool for AASI using Pint.
Provides verified unit conversions between engineering and astronomical units.
"""

from typing import Any, Dict, List
import pint

# Initialize global Pint UnitRegistry
ureg = pint.UnitRegistry()

# Supported conversion dimensions and common units
SUPPORTED_UNITS: Dict[str, List[str]] = {
    "distance": ["km", "m", "kilometer", "meter", "nmi", "mi", "ft", "au"],
    "velocity": ["km/s", "m/s", "knot", "mph", "ft/s"],
    "mass": ["kg", "tonne", "t", "g", "lb", "slug"],
    "time": ["s", "sec", "second", "min", "minute", "hr", "hour", "day", "yr", "year"],
    "acceleration": ["m/s^2", "km/s^2", "g0", "ft/s^2"],
}


def convert_unit(
    value: float,
    from_unit: str,
    to_unit: str,
) -> Dict[str, Any]:
    """
    Convert a numerical value from one unit to another using Pint.
    Ensures dimensional consistency and prevents dimension mismatch errors.
    """
    try:
        qty = value * ureg(from_unit.strip())
    except Exception as exc:
        raise ValueError(f"Unknown or invalid source unit '{from_unit}': {str(exc)}")

    try:
        target_qty = qty.to(to_unit.strip())
    except pint.DimensionalityError as exc:
        raise ValueError(
            f"Dimensionality mismatch: cannot convert '{from_unit}' ({qty.dimensionality}) "
            f"to '{to_unit}' ({ureg(to_unit).dimensionality})."
        )
    except Exception as exc:
        raise ValueError(f"Unknown or invalid target unit '{to_unit}': {str(exc)}")

    return {
        "tool": "units",
        "calculation": "unit_conversion",
        "inputs": {
            "value": value,
            "from_unit": from_unit,
            "to_unit": to_unit,
        },
        "results": {
            "converted_value": round(float(target_qty.magnitude), 6),
            "dimensionality": str(qty.dimensionality),
            "from_unit_canonical": str(qty.units),
            "to_unit_canonical": str(target_qty.units),
        },
        "units": {
            "source": from_unit,
            "target": to_unit,
        },
        "assumptions": [
            "Standard SI / CODATA base definitions",
            "Linear dimensional scale transformations",
        ],
    }
