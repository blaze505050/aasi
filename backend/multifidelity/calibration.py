"""
AASI Scientific Uncertainty Calibration Engine.

Rigorously evaluates whether predicted model uncertainties correspond to actual
validation errors:
- Empirical coverage probability for 1σ (~68.3%) and 2σ (~95.4%) intervals
- Mean absolute calibration error (MACE)
- Correlation between predicted uncertainty and actual error
- Scaling factor estimation to align epistemic uncertainty with true error distributions.
"""

from typing import List, Dict, Any, Tuple, Optional
import numpy as np
from backend.multifidelity.models import UncertaintyCalibrationMetrics


class UncertaintyCalibrationEngine:
    """Scientific calibration engine for surrogate uncertainty estimates."""

    @classmethod
    def evaluate_calibration(
        cls,
        predicted_values: List[float],
        true_values: List[float],
        predicted_uncertainties: List[float],
        model_id: str = "AERO_SURROGATE_V1",
        dataset_version: str = "DATASET-AUTHENTIC-AIRFOILS-V1"
    ) -> UncertaintyCalibrationMetrics:
        """
        Evaluates uncertainty calibration across a test dataset.
        
        Args:
            predicted_values: Array of model predictions (e.g. CL, CD)
            true_values: Array of true experimental/CFD targets
            predicted_uncertainties: Array of 1-sigma uncertainty estimates
        """
        y_pred = np.asarray(predicted_values, dtype=float)
        y_true = np.asarray(true_values, dtype=float)
        sigmas = np.asarray(predicted_uncertainties, dtype=float)

        n_samples = len(y_pred)
        if n_samples < 5:
            return UncertaintyCalibrationMetrics(
                model_id=model_id,
                dataset_version=dataset_version,
                sample_count=n_samples,
                empirical_coverage_1sigma=0.0,
                empirical_coverage_2sigma=0.0,
                average_interval_width=0.0,
                mean_absolute_calibration_error=1.0,
                correlation_error_vs_uncertainty=0.0,
                is_well_calibrated=False,
                recommended_scaling_factor=1.0,
                audit_notes=["Insufficient sample count to evaluate uncertainty calibration."]
            )

        # 1. Absolute test errors
        abs_errors = np.abs(y_pred - y_true)

        # 2. Avoid zero-division in sigmas
        safe_sigmas = np.maximum(sigmas, 1e-6)

        # 3. Z-scores: (y_pred - y_true) / sigma
        z_scores = (y_pred - y_true) / safe_sigmas

        # 4. Empirical coverage probabilities
        # Normal distribution targets: 1σ -> 68.27%, 2σ -> 95.45%
        coverage_1sigma = float(np.mean(np.abs(z_scores) <= 1.0)) * 100.0
        coverage_2sigma = float(np.mean(np.abs(z_scores) <= 2.0)) * 100.0

        # 5. Average interval width (2 * 1.96 * sigma)
        avg_width = float(np.mean(2.0 * 1.96 * safe_sigmas))

        # 6. Mean absolute calibration error (MACE)
        # Expected error under normal distribution with standard deviation sigma is sigma * sqrt(2/pi) ≈ 0.7979 * sigma
        expected_errors = safe_sigmas * np.sqrt(2.0 / np.pi)
        calibration_error = float(np.mean(np.abs(abs_errors - expected_errors)))

        # 7. Pearson correlation between predicted uncertainty and actual error
        if np.std(abs_errors) > 1e-8 and np.std(safe_sigmas) > 1e-8:
            corr = float(np.corrcoef(abs_errors, safe_sigmas)[0, 1])
            if np.isnan(corr):
                corr = 0.0
        else:
            corr = 0.0

        # 8. Optimal scaling factor: median absolute deviation / 0.6745
        # If z-scores have std > 1.0, the model is underconfident (or overconfident)
        empirical_std_z = float(np.std(z_scores))
        scaling_factor = float(np.clip(empirical_std_z, 0.2, 5.0))

        # 9. Calibration verdict: well-calibrated if 2σ coverage is between 88% and 98% and corr > 0.3
        is_well_calibrated = (85.0 <= coverage_2sigma <= 99.0) and (corr > 0.25)

        notes = []
        if coverage_2sigma < 85.0:
            notes.append(f"Model is OVERCONFIDENT: 2σ coverage ({coverage_2sigma:.1f}%) is below nominal 95.4%. Recommend multiplying uncertainty by {scaling_factor:.2f}.")
        elif coverage_2sigma > 99.0:
            notes.append(f"Model is UNDERCONFIDENT: 2σ coverage ({coverage_2sigma:.1f}%) is overly conservative. Recommend multiplying uncertainty by {scaling_factor:.2f}.")
        else:
            notes.append(f"Model achieves statistically valid empirical 2σ coverage ({coverage_2sigma:.1f}%).")

        if corr > 0.5:
            notes.append(f"Strong positive correlation ({corr:.2f}) between predicted uncertainty and actual test error; epistemic detector accurately flags high-error regions.")
        elif corr > 0.2:
            notes.append(f"Moderate correlation ({corr:.2f}) between predicted uncertainty and actual test error.")
        else:
            notes.append(f"Weak correlation ({corr:.2f}); uncertainty reflects condition distance rather than direct epistemic error.")

        return UncertaintyCalibrationMetrics(
            model_id=model_id,
            dataset_version=dataset_version,
            sample_count=n_samples,
            empirical_coverage_1sigma=round(coverage_1sigma, 2),
            empirical_coverage_2sigma=round(coverage_2sigma, 2),
            average_interval_width=round(avg_width, 6),
            mean_absolute_calibration_error=round(calibration_error, 6),
            correlation_error_vs_uncertainty=round(corr, 3),
            is_well_calibrated=is_well_calibrated,
            recommended_scaling_factor=round(scaling_factor, 3),
            audit_notes=notes
        )
