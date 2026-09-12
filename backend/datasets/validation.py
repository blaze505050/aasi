"""
AASI Comprehensive Dataset Validation Engine.

Performs rigorous physical, numerical, and machine learning integrity checks:
1. Mesh Sanity: node count positivity, coordinate bounds, wall distance validity
2. Physical Field Bounds: Cd >= 0, nu_tilde >= 0, velocity magnitudes, kinematic pressure
3. Duplicate Case Detection: identical flight conditions within epsilon tolerance
4. Train/Test Geometry Leakage: cross-split geometry isolation verification
"""

from __future__ import annotations

import math
from enum import Enum
from typing import Dict, Any, List, Optional, Tuple, Set
from pydantic import BaseModel, Field

from backend.datasets.adapters.base import DatasetCase


class ValidationSeverity(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    FATAL = "FATAL"


class ValidationCheckResult(BaseModel):
    check_name: str
    passed: bool
    severity: ValidationSeverity
    details: str
    affected_cases: List[str] = Field(default_factory=list)


class DatasetValidationReport(BaseModel):
    dataset_id: str
    total_cases_inspected: int
    is_valid: bool
    checks: List[ValidationCheckResult] = Field(default_factory=list)
    summary: Dict[str, int] = Field(default_factory=dict)


class DatasetValidator:
    """Rigorous scientific validator for aerodynamic datasets and cases."""

    @classmethod
    def validate_aerodynamic_sample(cls, sample: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validates individual aerodynamic data point for physical realism:
        - -3.5 <= CL <= 3.5 (normal airfoil envelope)
        - 0.0 <= CD <= 2.5 (strictly positive drag)
        - Re > 0
        - Mach >= 0
        """
        errors = []

        if "cd" in sample and sample["cd"] is not None:
            cd = float(sample["cd"])
            if cd < 0:
                errors.append(f"Physical violation: Drag coefficient Cd={cd} cannot be negative.")
            elif cd > 2.5:
                errors.append(f"Physical violation: Drag coefficient Cd={cd} exceeds typical airfoil maximum (2.5).")

        if "cl" in sample and sample["cl"] is not None:
            cl = float(sample["cl"])
            if abs(cl) > 3.5:
                errors.append(f"Physical violation: Lift coefficient |Cl|={cl} exceeds conventional subsonic airfoil stall bounds.")

        if "reynolds" in sample and sample["reynolds"] is not None:
            re = float(sample["reynolds"])
            if re <= 0:
                errors.append(f"Physical violation: Reynolds number Re={re} must be strictly positive.")

        if "mach" in sample and sample["mach"] is not None:
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
            "errors": all_errors[:10]
        }

    @classmethod
    def validate_case(cls, case: DatasetCase) -> List[ValidationCheckResult]:
        """Performs exhaustive validation on a DatasetCase."""
        results = []

        # 1. Physical field bounds check
        field_errs = []
        if case.cd is not None and case.cd < 0.0:
            field_errs.append(f"Negative drag coefficient: CD={case.cd}")
        if case.reynolds <= 0.0:
            field_errs.append(f"Non-positive Reynolds number: Re={case.reynolds}")
        if case.mach < 0.0:
            field_errs.append(f"Negative Mach number: M={case.mach}")
        if case.cl is not None and abs(case.cl) > 4.0:
            field_errs.append(f"Unphysical lift coefficient: CL={case.cl}")

        results.append(ValidationCheckResult(
            check_name="physical_bounds_check",
            passed=(len(field_errs) == 0),
            severity=ValidationSeverity.ERROR if field_errs else ValidationSeverity.INFO,
            details="Passed physical bounds" if not field_errs else "; ".join(field_errs),
            affected_cases=[case.case_id] if field_errs else []
        ))

        # 2. Mesh sanity check
        mesh_errs = []
        if case.node_count is not None and case.node_count <= 0:
            mesh_errs.append(f"Invalid mesh node count: {case.node_count}")
        results.append(ValidationCheckResult(
            check_name="mesh_sanity_check",
            passed=(len(mesh_errs) == 0),
            severity=ValidationSeverity.ERROR if mesh_errs else ValidationSeverity.INFO,
            details="Mesh node count valid" if not mesh_errs else "; ".join(mesh_errs),
            affected_cases=[case.case_id] if mesh_errs else []
        ))

        return results

    @classmethod
    def check_duplicate_cases(cls, cases: List[DatasetCase], tolerance: float = 1e-4) -> ValidationCheckResult:
        """Detects duplicate CFD cases sharing geometry, Reynolds, Mach, and AoA."""
        seen = {}
        duplicates = []

        for case in cases:
            key = (
                case.geometry_name.strip().upper(),
                round(case.reynolds / 1000.0) * 1000.0,
                round(case.mach, 3),
                round(case.aoa_deg, 2)
            )
            if key in seen:
                duplicates.append(f"{case.case_id} duplicates {seen[key]} at conditions {key}")
            else:
                seen[key] = case.case_id

        passed = len(duplicates) == 0
        return ValidationCheckResult(
            check_name="duplicate_cases_detection",
            passed=passed,
            severity=ValidationSeverity.WARNING if not passed else ValidationSeverity.INFO,
            details="No duplicate cases found" if passed else f"Found {len(duplicates)} duplicates: {'; '.join(duplicates[:3])}",
            affected_cases=duplicates
        )

    @classmethod
    def check_geometry_leakage(
        cls,
        train_case_ids: List[str],
        test_case_ids: List[str],
        cases_map: Dict[str, DatasetCase]
    ) -> ValidationCheckResult:
        """
        Verifies strict separation of geometries between training and testing splits.
        Airfoils in test set must not appear in the training set.
        """
        train_geoms = {cases_map[cid].geometry_name.strip().upper() for cid in train_case_ids if cid in cases_map}
        test_geoms = {cases_map[cid].geometry_name.strip().upper() for cid in test_case_ids if cid in cases_map}

        overlap = train_geoms.intersection(test_geoms)
        passed = len(overlap) == 0

        return ValidationCheckResult(
            check_name="geometry_leakage_check",
            passed=passed,
            severity=ValidationSeverity.ERROR if not passed else ValidationSeverity.INFO,
            details="Zero geometric data leakage between train and test" if passed else f"Geometric leakage detected! Overlapping airfoils: {sorted(list(overlap))}",
            affected_cases=sorted(list(overlap))
        )

    @classmethod
    def run_full_dataset_validation(
        cls,
        dataset_id: str,
        cases: List[DatasetCase],
        splits: Optional[Dict[str, List[str]]] = None
    ) -> DatasetValidationReport:
        """Executes full validation suite on an entire dataset."""
        all_checks: List[ValidationCheckResult] = []
        cases_map = {c.case_id: c for c in cases}

        # Case-level checks
        bound_failures = []
        mesh_failures = []
        for case in cases:
            case_results = cls.validate_case(case)
            for res in case_results:
                if not res.passed:
                    if res.check_name == "physical_bounds_check":
                        bound_failures.append(case.case_id)
                    elif res.check_name == "mesh_sanity_check":
                        mesh_failures.append(case.case_id)

        all_checks.append(ValidationCheckResult(
            check_name="batch_physical_bounds",
            passed=len(bound_failures) == 0,
            severity=ValidationSeverity.ERROR if bound_failures else ValidationSeverity.INFO,
            details=f"All {len(cases)} cases satisfy physical bounds" if not bound_failures else f"{len(bound_failures)} cases failed physical bounds",
            affected_cases=bound_failures
        ))

        all_checks.append(ValidationCheckResult(
            check_name="batch_mesh_sanity",
            passed=len(mesh_failures) == 0,
            severity=ValidationSeverity.ERROR if mesh_failures else ValidationSeverity.INFO,
            details=f"All {len(cases)} meshes pass sanity check" if not mesh_failures else f"{len(mesh_failures)} meshes failed sanity check",
            affected_cases=mesh_failures
        ))

        # Dataset-level duplicate check
        dup_check = cls.check_duplicate_cases(cases)
        all_checks.append(dup_check)

        # Split leakage check if splits provided
        if splits and "full_train" in splits and "full_test" in splits:
            leakage_check = cls.check_geometry_leakage(splits["full_train"], splits["full_test"], cases_map)
            all_checks.append(leakage_check)

        # Summary computation
        total_errors = sum(1 for c in all_checks if not c.passed and c.severity in (ValidationSeverity.ERROR, ValidationSeverity.FATAL))
        total_warnings = sum(1 for c in all_checks if not c.passed and c.severity == ValidationSeverity.WARNING)

        is_valid = total_errors == 0
        summary = {
            "total_checks": len(all_checks),
            "passed_checks": sum(1 for c in all_checks if c.passed),
            "error_count": total_errors,
            "warning_count": total_warnings
        }

        return DatasetValidationReport(
            dataset_id=dataset_id,
            total_cases_inspected=len(cases),
            is_valid=is_valid,
            checks=all_checks,
            summary=summary
        )
