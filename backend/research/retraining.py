"""
AASI Autonomous Retraining Orchestrator.

Manages the retraining lifecycle:
Augmented Dataset -> Surrogate Training -> Fixed Benchmarking -> Model Comparison -> Promotion Audit.
"""

from typing import Dict, List, Optional, Any
from pathlib import Path
from pydantic import BaseModel, Field
from datetime import datetime, timezone
import json
import os
import numpy as np

from backend.physics_ai.schemas import TrainingRunConfig
from backend.physics_ai.training import SurrogateTrainer
from backend.physics_ai.checkpoints import CheckpointManager
from backend.research.benchmarks import FixedBenchmarkSuite, BenchmarkEvaluationResult
from backend.research.comparison import ModelComparisonEngine, ModelComparisonReport
from backend.research.promotion import ModelPromotionPipeline, ModelPromotionAudit, PromotionTier
from backend.datasets.versioning import dataset_version_manager


class RetrainingSummary(BaseModel):
    training_run_id: str
    dataset_version: str
    model_version: str
    checkpoint_path: str
    checksum: str
    benchmark_evaluation: BenchmarkEvaluationResult
    comparison_with_baseline: ModelComparisonReport
    promotion_audit: ModelPromotionAudit
    completed_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class RetrainingOrchestrator:
    """Orchestrates autonomous retraining of aerodynamic surrogate models."""

    @classmethod
    def execute_retraining_loop(
        cls,
        dataset_version_id: str = "AERO-AIRFOIL-V2.0",
        epochs: int = 10,
        baseline_checkpoint: str = "aero_surrogate_v1.npz",
        candidate_filename: str = "aero_surrogate_v2.npz"
    ) -> RetrainingSummary:
        """
        Executes end-to-end retraining, benchmark evaluation, comparison, and promotion.
        """
        run_id = f"RETRAIN-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        config = TrainingRunConfig(
            training_run_id=run_id,
            epochs=epochs,
            batch_size=32,
            learning_rate=0.001,
            seed=42
        )

        # 1. Run CPU-friendly training
        trainer = SurrogateTrainer(config=config, runs_base_dir=f"data/training_runs/{run_id}")
        train_results = trainer.run_training()

        # 2. Save candidate checkpoint
        ckpt_mgr = CheckpointManager(checkpoints_dir="data/checkpoints")
        ckpt_path, checksum = ckpt_mgr.save_checkpoint(
            model=train_results["model"],
            condition_normalizer=train_results["dataset"].condition_normalizer,
            target_scaler=train_results["dataset"].target_scaler,
            training_metadata={
                "model_version": "AeroSurrogateV2",
                "parent_version": "AeroSurrogateV1",
                "dataset_version": dataset_version_id,
                "epochs": epochs,
                "run_id": run_id
            },
            filename=candidate_filename
        )

        # 3. Build prediction callable for candidate
        norm = train_results["dataset"].condition_normalizer
        scaler = train_results["dataset"].target_scaler
        model = train_results["model"]

        # Cache geometry coordinates for benchmark airfoils
        from backend.physics_ai.geometry import AirfoilGeometryEncoder
        geom_coords = {
            "NACA 0012": AirfoilGeometryEncoder.naca4_coordinates("0012", n_points=128),
            "NACA 2412": AirfoilGeometryEncoder.naca4_coordinates("2412", n_points=128),
            "NACA 4412": AirfoilGeometryEncoder.naca4_coordinates("4412", n_points=128),
        }

        def candidate_predict(geom: str, mach: float, re: float, aoa: float) -> Dict[str, float]:
            coords = geom_coords.get(geom, geom_coords["NACA 0012"])[np.newaxis, :, :]
            cond = norm.transform(np.array([[mach, np.log10(max(re, 1e4)), aoa]]))
            pred_norm = model.forward(coords, cond)
            pred_phys = scaler.inverse_transform(pred_norm)[0]
            return {"cl": float(pred_phys[0]), "cd": max(0.0001, float(pred_phys[1])), "cm": float(pred_phys[2])}

        # 4. Build prediction callable for baseline
        try:
            base_model, base_norm, base_scaler, _ = ckpt_mgr.load_checkpoint(baseline_checkpoint)
            def baseline_predict(geom: str, mach: float, re: float, aoa: float) -> Dict[str, float]:
                coords = geom_coords.get(geom, geom_coords["NACA 0012"])[np.newaxis, :, :]
                cond = base_norm.transform(np.array([[mach, np.log10(max(re, 1e4)), aoa]]))
                pred_norm = base_model.forward(coords, cond)
                pred_phys = base_scaler.inverse_transform(pred_norm)[0]
                return {"cl": float(pred_phys[0]), "cd": max(0.0001, float(pred_phys[1])), "cm": float(pred_phys[2])}
        except Exception:
            baseline_predict = candidate_predict

        # 5. Fixed benchmark evaluation
        bench_eval = FixedBenchmarkSuite.evaluate_model(candidate_predict)

        # 6. Model comparison
        comparison = ModelComparisonEngine.compare_models(
            baseline_id="AeroSurrogateV1",
            candidate_id="AeroSurrogateV2",
            baseline_predict_fn=baseline_predict,
            candidate_predict_fn=candidate_predict
        )

        # 7. Model promotion audit
        promotion = ModelPromotionPipeline.evaluate_promotion(
            candidate_id="AeroSurrogateV2",
            baseline_id="AeroSurrogateV1",
            candidate_predict_fn=candidate_predict,
            baseline_predict_fn=baseline_predict
        )

        return RetrainingSummary(
            training_run_id=run_id,
            dataset_version=dataset_version_id,
            model_version="AeroSurrogateV2",
            checkpoint_path=str(ckpt_path),
            checksum=checksum,
            benchmark_evaluation=bench_eval,
            comparison_with_baseline=comparison,
            promotion_audit=promotion
        )
