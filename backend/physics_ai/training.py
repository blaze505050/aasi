"""
AASI Surrogate Training Runner.

Executes reproducible, pure-CPU training of AeroSurrogateV1:
- Enforces strict random seeds
- Uses weighted multi-target loss (L = w_cl*L_cl + w_cd*L_cd + w_cm*L_cm)
- Vectorized AdamW optimizer with cosine learning rate schedule
- Evaluates train, validation, test, and OOD sets
- Benchmarks against Ridge, Random Forest, and MLP baselines
- Runs automated physics-aware validation checks
- Saves weights checkpoint and training run artifacts (config, metrics, environment, provenance).
"""

import os
import json
import random
from pathlib import Path
from typing import Dict, Any, Tuple, Optional, List
import numpy as np

from backend.physics_ai.schemas import TrainingRunConfig, EvaluationMetrics
from backend.physics_ai.models import AeroSurrogateV1
from backend.physics_ai.dataset import AerodynamicAirfoilDataset
from backend.physics_ai.splits import GeometryLevelSplitter
from backend.physics_ai.metrics import AerodynamicEvaluator
from backend.physics_ai.validation import PhysicsAwareValidator
from backend.physics_ai.baselines import AerodynamicBaselines
from backend.physics_ai.checkpoints import CheckpointManager
from backend.physics_ai.provenance import TrainingProvenanceLogger
from backend.physics_ai.normalization import FlowConditionNormalizer, AerodynamicTargetScaler
from backend.physics_ai.governance import HardwareGovernanceGuard
from backend.physics_ai.reproducibility import TrainingReproducibilityManifest
from backend.physics_ai.report import ModelExperimentReportGenerator
from backend.physics.training_models import ModelLifecycleStatus


class NumpyAdamW:
    """Vectorized AdamW optimizer for NumPy parameter dictionaries."""

    def __init__(
        self,
        params: Dict[str, np.ndarray],
        lr: float = 1e-3,
        beta1: float = 0.9,
        beta2: float = 0.999,
        eps: float = 1e-8,
        weight_decay: float = 1e-4
    ):
        self.params = params
        self.lr = lr
        self.initial_lr = lr
        self.beta1 = beta1
        self.beta2 = beta2
        self.eps = eps
        self.weight_decay = weight_decay
        self.t = 0
        self.m = {k: np.zeros_like(v) for k, v in params.items()}
        self.v = {k: np.zeros_like(v) for k, v in params.items()}

    def set_lr(self, lr: float):
        self.lr = lr

    def step(self, grads: Dict[str, np.ndarray]):
        self.t += 1
        lr_t = self.lr * np.sqrt(1.0 - self.beta2 ** self.t) / (1.0 - self.beta1 ** self.t)
        for k in self.params:
            if k not in grads:
                continue
            g = grads[k]
            self.m[k] = self.beta1 * self.m[k] + (1.0 - self.beta1) * g
            self.v[k] = self.beta2 * self.v[k] + (1.0 - self.beta2) * (g ** 2)
            # Adam step + decoupled weight decay
            update = lr_t * self.m[k] / (np.sqrt(self.v[k]) + self.eps)
            if self.weight_decay > 0:
                self.params[k] -= self.lr * self.weight_decay * self.params[k]
            self.params[k] -= update


class SurrogateTrainer:
    """Orchestrates reproducible training and evaluation for AeroSurrogateV1."""

    def __init__(self, config: Optional[TrainingRunConfig] = None):
        self.config = config or TrainingRunConfig(
            training_run_id="TR-AERO-SURROGATE-V1-001",
            epochs=150,
            batch_size=32,
            learning_rate=0.003,
            weight_decay=1e-4,
            seed=42
        )
        self._set_seeds(self.config.seed)

    def _set_seeds(self, seed: int):
        random.seed(seed)
        np.random.seed(seed)

    def run_training(
        self,
        data_dir: str = "data/datasets/authentic_airfoils",
        output_dir: str = "data/training_runs",
        export_to_shared: bool = False
    ) -> Dict[str, Any]:
        """Loads data, partitions via geometry-level split, trains AeroSurrogateV1, evaluates all splits."""
        # 0. Pre-flight Hardware & Performance Governance Check
        gov_report = HardwareGovernanceGuard.evaluate_training_feasibility(
            sample_count=2000,
            epochs=self.config.epochs,
            batch_size=self.config.batch_size,
        )
        if not gov_report.is_safe:
            raise RuntimeError(f"RESOURCE_LIMITED: {gov_report.recommendation}")

        # 1. Load authentic dataset (without peeking for normalizers)
        dataset = AerodynamicAirfoilDataset.load_from_directory(data_dir=data_dir, fit_normalizers=False)

        # 2. Geometry-level leakage-free split
        splitter = GeometryLevelSplitter(seed=self.config.seed)
        split_dict = splitter.split_samples(dataset.samples)

        # Phase 9: Fit normalization/scaling strictly on training data ONLY
        train_samples = split_dict["train"]
        cond_norm = FlowConditionNormalizer()
        targ_scale = AerodynamicTargetScaler()
        train_conds = np.array([[s.mach, s.reynolds, s.aoa_deg] for s in train_samples], dtype=np.float32)
        train_targs = np.array([[s.cl, s.cd, s.cm] for s in train_samples], dtype=np.float32)
        cond_norm.fit(train_conds)
        targ_scale.fit(train_targs)

        train_ds = AerodynamicAirfoilDataset(
            split_dict["train"], dataset.geometries,
            condition_normalizer=cond_norm,
            target_scaler=targ_scale
        )
        val_ds = AerodynamicAirfoilDataset(
            split_dict["val"], dataset.geometries,
            condition_normalizer=cond_norm,
            target_scaler=targ_scale
        )
        test_ds = AerodynamicAirfoilDataset(
            split_dict["test"], dataset.geometries,
            condition_normalizer=cond_norm,
            target_scaler=targ_scale
        )
        ood_ds = AerodynamicAirfoilDataset(
            split_dict["ood_geometry"], dataset.geometries,
            condition_normalizer=cond_norm,
            target_scaler=targ_scale
        )

        # 3. Extract feature arrays for train / val
        def get_arrays(ds: AerodynamicAirfoilDataset):
            n = len(ds)
            geom_arr = np.zeros((n, ds.coords_points, 2), dtype=np.float32)
            cond_arr = ds.norm_conditions.astype(np.float32)
            targ_arr = ds.norm_targets.astype(np.float32)
            for i in range(n):
                geom_arr[i] = ds.geom_tensors[ds.samples[i].geometry]
            return geom_arr, cond_arr, targ_arr

        X_geom_train, X_cond_train, y_train = get_arrays(train_ds)
        X_geom_val, X_cond_val, y_val = get_arrays(val_ds)
        X_geom_test, X_cond_test, y_test = get_arrays(test_ds)

        # 4. Initialize Model & Optimizer
        model = AeroSurrogateV1(seed=self.config.seed)
        optimizer = NumpyAdamW(
            model.params,
            lr=self.config.learning_rate,
            weight_decay=self.config.weight_decay
        )

        # Multi-target weighted loss
        w_cl = self.config.loss_weights.get("cl", 1.0)
        w_cd = self.config.loss_weights.get("cd", 5.0)
        w_cm = self.config.loss_weights.get("cm", 2.0)
        weights_vec = np.array([w_cl, w_cd, w_cm], dtype=np.float32)

        # 5. Training Loop
        history = {"train_loss": [], "val_loss": []}
        best_val_loss = float("inf")
        best_params = {k: v.copy() for k, v in model.params.items()}

        n_train = len(train_ds)
        batch_size = self.config.batch_size
        epochs = self.config.epochs

        for epoch in range(1, epochs + 1):
            # Cosine learning rate schedule
            lr = self.config.learning_rate * 0.5 * (1.0 + np.cos(np.pi * (epoch - 1) / epochs))
            optimizer.set_lr(max(lr, 1e-4))

            # Shuffle mini-batches
            indices = np.random.permutation(n_train)
            total_train_loss = 0.0

            for start_idx in range(0, n_train, batch_size):
                batch_idx = indices[start_idx:start_idx + batch_size]
                b_geom = X_geom_train[batch_idx]
                b_cond = X_cond_train[batch_idx]
                b_targ = y_train[batch_idx]

                preds, cache = model.forward(b_geom, b_cond, return_intermediates=True)
                diff = preds - b_targ  # [B, 3]

                batch_loss = np.mean(weights_vec * (diff ** 2))
                total_train_loss += batch_loss * len(batch_idx)

                # Analytical gradient w.r.t model output: dL/dout = 2 * weights * diff
                d_out = 2.0 * weights_vec * diff
                grads = model.backward(d_out, cache)
                optimizer.step(grads)

            train_loss = total_train_loss / n_train
            history["train_loss"].append(round(float(train_loss), 6))

            # Validation pass
            val_preds = model.forward(X_geom_val, X_cond_val)
            val_diff = val_preds - y_val
            val_loss = float(np.mean(weights_vec * (val_diff ** 2)))
            history["val_loss"].append(round(val_loss, 6))

            if val_loss < best_val_loss:
                best_val_loss = val_loss
                best_params = {k: v.copy() for k, v in model.params.items()}

        # Load best parameters
        model.params = best_params

        # 6. Evaluate all splits
        test_metrics = self._evaluate_split(model, test_ds, X_geom_test, X_cond_test, "test")
        val_metrics = self._evaluate_split(model, val_ds, X_geom_val, X_cond_val, "val")
        train_metrics = self._evaluate_split(model, train_ds, X_geom_train, X_cond_train, "train")

        ood_metrics = None
        if len(ood_ds) > 0:
            X_geom_ood, X_cond_ood, _ = get_arrays(ood_ds)
            ood_metrics = self._evaluate_split(model, ood_ds, X_geom_ood, X_cond_ood, "ood_geometry")

        # 7. Benchmarks against Baselines
        # Flatten geometry contours + condition for tabular baselines
        X_tab_train = np.concatenate([X_geom_train.reshape(n_train, -1), train_ds.raw_conditions], axis=1)
        X_tab_test = np.concatenate([X_geom_test.reshape(len(test_ds), -1), test_ds.raw_conditions], axis=1)
        baselines = AerodynamicBaselines(random_state=self.config.seed)
        baseline_results = baselines.fit_and_evaluate(
            X_train=X_tab_train,
            y_train=train_ds.raw_targets,
            X_test=X_tab_test,
            y_test=test_ds.raw_targets
        )

        # 8. Physics-Aware Validation Checks
        test_norm_preds = model.forward(X_geom_test, X_cond_test)
        test_phys_preds = test_ds.target_scaler.inverse_transform(test_norm_preds)
        val_report = PhysicsAwareValidator.validate_predictions(
            geometries=test_ds.sample_geoms,
            aoas=test_ds.raw_conditions[:, 2],
            cl_preds=test_phys_preds[:, 0],
            cd_preds=test_phys_preds[:, 1],
            cm_preds=test_phys_preds[:, 2]
        )


        # 9. Save Checkpoint & Training Run Directory
        run_dir = Path(output_dir) / self.config.training_run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        ckpt_dir = run_dir / "checkpoints"
        ckpt_dir.mkdir(parents=True, exist_ok=True)

        ckpt_mgr = CheckpointManager(checkpoints_dir=str(ckpt_dir))
        metadata = {
            "training_run_id": self.config.training_run_id,
            "test_metrics": test_metrics.model_dump(),
            "val_metrics": val_metrics.model_dump(),
            "train_metrics": train_metrics.model_dump(),
            "ood_metrics": ood_metrics.model_dump() if ood_metrics else None,
            "epochs": self.config.epochs,
            "parameters": model.count_parameters(),
        }
        ckpt_path, checksum = ckpt_mgr.save_checkpoint(
            model=model,
            condition_normalizer=cond_norm,
            target_scaler=targ_scale,
            training_metadata=metadata,
            filename="aero_surrogate_v1.npz"
        )

        # Also save to shared production checkpoint directory if explicitly requested
        if export_to_shared:
            shared_ckpt_mgr = CheckpointManager(checkpoints_dir="data/checkpoints")
            shared_ckpt_mgr.save_checkpoint(
                model=model,
                condition_normalizer=cond_norm,
                target_scaler=targ_scale,
                training_metadata=metadata,
                filename="aero_surrogate_v1.npz"
            )

        # Audit promotion gates
        can_promote, promo_violations = PhysicsAwareValidator.audit_model_promotion_gates(
            metrics={"cl_rmse": test_metrics.cl_rmse, "r2": test_metrics.cl_r2},
            physics_report=val_report
        )
        lifecycle_status = ModelLifecycleStatus.VERIFIED if can_promote else ModelLifecycleStatus.TRAINED_UNVERIFIED

        # Generate Phase 10 Reproducibility Manifest
        repro_manifest = TrainingReproducibilityManifest.create_and_sign(
            run_id=self.config.training_run_id,
            training_dataset_id="DATASET-AUTHENTIC-AIRFOILS-V1",
            training_dataset_hash=split_dict["manifest"].get("split_checksum", ""),
            validation_dataset_hash=split_dict["manifest"].get("split_checksum", ""),
            test_dataset_hash=split_dict["manifest"].get("split_checksum", ""),
            geometry_split_manifest_hash=split_dict["manifest"].get("split_checksum", ""),
            hyperparameters=self.config.model_dump(),
            checkpoint_file=ckpt_path.name,
            checkpoint_sha256=checksum,
            training_metrics=train_metrics.model_dump(),
            validation_metrics=val_metrics.model_dump(),
            test_metrics=test_metrics.model_dump(),
            ood_metrics=ood_metrics.model_dump() if ood_metrics else {},
            physics_validation_summary=val_report,
            normalization_params={"condition": cond_norm.to_dict(), "target": targ_scale.to_dict()},
            uncertainty_config={"validity_envelope": {"mach": [0.05, 0.40], "reynolds": [5e5, 6e6], "aoa_deg": [-8.0, 18.0]}},
            seed=self.config.seed
        )

        # Generate Phase 13 & 14 Formal Scientific Report
        scientific_report = ModelExperimentReportGenerator.generate_report(
            run_id=self.config.training_run_id,
            research_question="Can a lightweight neural operator learn authentic 2D airfoil polars with zero data leakage and drag positivity?",
            dataset_manifest={
                "name": "Authentic 2D Airfoil Geometry & Aerodynamic Polar Benchmark",
                "source": "NACA / Abbott & von Doenhoff / Validated RANS",
                "license": "Public Domain",
                "experimental_or_simulated": "EXPERIMENTAL",
                "checksum": split_dict["manifest"].get("split_checksum", "")
            },
            split_manifest=split_dict["manifest"],
            model_config={"model_name": model.model_id, "parameters": model.count_parameters(), "seed": self.config.seed},
            test_metrics=test_metrics.model_dump(),
            ood_metrics=ood_metrics.model_dump() if ood_metrics else None,
            physics_report=val_report,
            reproducibility_manifest=repro_manifest.model_dump()
        )

        # Write artifacts
        (run_dir / "config.json").write_text(json.dumps(self.config.model_dump(), indent=2), encoding="utf-8")
        (run_dir / "split_manifest.json").write_text(json.dumps(split_dict["manifest"], indent=2), encoding="utf-8")
        (run_dir / "baselines.json").write_text(json.dumps(baseline_results, indent=2), encoding="utf-8")
        (run_dir / "physics_validation.json").write_text(json.dumps(val_report, indent=2), encoding="utf-8")
        (run_dir / "reproducibility_manifest.json").write_text(json.dumps(repro_manifest.model_dump(), indent=2), encoding="utf-8")
        (run_dir / "scientific_report.md").write_text(scientific_report, encoding="utf-8")

        (run_dir / "metrics.json").write_text(json.dumps({
            "test": test_metrics.model_dump(),
            "val": val_metrics.model_dump(),
            "train": train_metrics.model_dump(),
            "ood_geometry": ood_metrics.model_dump() if ood_metrics else None,
            "physics_validation": val_report,
            "lifecycle_status": lifecycle_status.value,
            "history": history
        }, indent=2), encoding="utf-8")

        provenance = TrainingProvenanceLogger.capture_environment(
            seed=self.config.seed,
            split_checksum=split_dict["manifest"].get("split_checksum", ""),
            training_config=self.config.model_dump()
        )
        (run_dir / "provenance.json").write_text(json.dumps(provenance, indent=2), encoding="utf-8")

        return {
            "training_run_id": self.config.training_run_id,
            "checkpoint_path": str(ckpt_path),
            "checksum": checksum,
            "parameters": model.count_parameters(),
            "lifecycle_status": lifecycle_status.value,
            "test_metrics": test_metrics,
            "val_metrics": val_metrics,
            "ood_metrics": ood_metrics,
            "baselines": baseline_results,
            "provenance": provenance,
            "reproducibility_manifest": repro_manifest.model_dump(),
            "scientific_report": scientific_report,
            "model": model,
            "dataset": dataset,
        }

    def _evaluate_split(
        self,
        model: AeroSurrogateV1,
        ds: AerodynamicAirfoilDataset,
        geom_coords: np.ndarray,
        norm_conditions: np.ndarray,
        split_name: str
    ) -> EvaluationMetrics:
        """Evaluates model on given dataset partition."""
        norm_pred = model.forward(geom_coords, norm_conditions)
        phys_pred = ds.target_scaler.inverse_transform(norm_pred)
        phys_true = ds.raw_targets

        return AerodynamicEvaluator.evaluate_predictions(
            y_true=phys_true,
            y_pred=phys_pred,
            split_name=split_name,
            geometries=ds.sample_geoms
        )


if __name__ == "__main__":
    trainer = SurrogateTrainer()
    results = trainer.run_training()
    print("Training complete!")
    print(f"Checksum: {results['checksum']}")
    print(f"Test CL RMSE: {results['test_metrics'].cl_rmse}, CD RMSE: {results['test_metrics'].cd_rmse}")
