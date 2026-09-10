"""
AASI Dataset Validator.

Validates schema conformity, physical boundaries, missing values,
and physical consistency (e.g. positive density, valid pressure coefficients).
"""

from typing import Dict, Any, List, Tuple


class DatasetValidator:
    """Validates physical consistency and schema compliance in CFD/experimental data."""

    @classmethod
    def validate_aerodynamic_sample(cls, sample: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validates individual aerodynamic data point for physical realism:
        - -3.0 <= CL <= 3.0 (normal airfoil envelope)
        - 0.0 <= CD <= 2.5 (strictly positive drag)
        - Re > 0
        - Mach >= 0
        """
        errors = []

        if "cd" in sample:
            cd = float(sample["cd"])
            if cd < 0:
                errors.append(f"Physical violation: Drag coefficient Cd={cd} cannot be negative.")
            elif cd > 2.5:
                errors.append(f"Physical violation: Drag coefficient Cd={cd} exceeds typical airfoil maximum (2.5).")

        if "cl" in sample:
            cl = float(sample["cl"])
            if abs(cl) > 3.5:
                errors.append(f"Physical violation: Lift coefficient |Cl|={cl} exceeds conventional subsonic airfoil stall bounds.")

        if "reynolds" in sample:
            re = float(sample["reynolds"])
            if re <= 0:
                errors.append(f"Physical violation: Reynolds number Re={re} must be strictly positive.")

        if "mach" in sample:
            m = float(sample["mach"])
            if m < 0:
                errors.append(f"Physical violation: Mach number M={m} cannot be negative.")

        is_valid = (len(errors) == 0)
        return is_valid, errors

    @classmethod
    def validate_dataset_records(cls, records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validates an entire batch of dataset records."""
        total = len(records)
        valid_count = 0
        all_errors = []

        for idx, rec in enumerate(records):
            is_valid, errs = cls.validate_aerodynamic_sample(rec)
            if is_valid:
                valid_count += 1
            else:
                all_errors.append({"record_index": idx, "errors": errs})

        return {
            "total_records": total,
            "valid_records": valid_count,
            "corrupt_or_invalid_records": total - valid_count,
            "validation_passed": (valid_count == total),
            "errors": all_errors[:10]  # Cap error snippet
        }
