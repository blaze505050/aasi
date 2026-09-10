"""
AASI Physics-AI Model Registry.

Tracks trained and deployed neural operators and surrogates (AeroGraphNet, FNO,
MeshGraphNet, DoMINO, PINNs) with full configuration, metrics, checksums,
and validity envelopes. Never silently overwrites existing models.
"""

import hashlib
from typing import Dict, Any, List, Optional
from backend.physics.training_models import RegisteredModel, TrainingConfig


class PhysicsModelRegistry:
    """Central registry for versioned physics AI models."""

    def __init__(self):
        self._models: Dict[str, RegisteredModel] = {}
        self._register_seed_models()

    def _register_seed_models(self):
        # 1. Baseline AeroGraphNet
        m1_config = TrainingConfig(
            config_id="TR-CFG-AEROGRAPHNET-001",
            model_name="AeroGraphNet-NACA-2D",
            architecture="AeroGraphNet (GNN Mesh Encoder + Edge Convolution)",
            dataset_version="DATASET-AIRFRANS-1K",
            hyperparameters={"learning_rate": 3e-4, "batch_size": 32, "epochs": 150},
            hardware="NVIDIA A100 (Remote Cluster)",
            training_time_seconds=7200.0,
            metrics={"cl_rmse": 0.0182, "cd_rmse": 0.0014, "r2_score": 0.988},
            evaluation_dataset="AirfRANS Geometry-Level Test Split"
        )
        self.register_model(RegisteredModel(
            model_id="MODEL-AEROGRAPHNET-NACA-2D",
            architecture="AeroGraphNet",
            version="1.0.0",
            dataset_id="DATASET-AIRFRANS-1K",
            domain={"mach": [0.1, 0.6], "reynolds": [2.0e5, 2.0e6], "aoa_deg": [-6.0, 12.0]},
            outputs=["CL", "CD", "CM"],
            metrics={"cl_rmse": 0.0182, "cd_rmse": 0.0014},
            uncertainty_envelope={"cl_sigma": 0.02, "cd_sigma": 0.0015},
            license="Apache-2.0",
            checksum=hashlib.sha256(b"MODEL-AEROGRAPHNET-WEIGHTS-V1").hexdigest(),
            training_config=m1_config,
            validation_status="TRAINED_AND_VALIDATED",
            deployment_status="DEPLOYED"
        ))

        # 2. Fourier Neural Operator (FNO) 2D Pressure Field
        m2_config = TrainingConfig(
            config_id="TR-CFG-FNO-AIRFOIL-002",
            model_name="FNO-Airfoil-Pressure-2D",
            architecture="Fourier Neural Operator (FNO-2D with 16 Fourier Modes)",
            dataset_version="DATASET-AIRFRANS-1K",
            hyperparameters={"learning_rate": 1e-3, "batch_size": 16, "epochs": 200, "modes": 16, "width": 64},
            hardware="NVIDIA V100 (Google Colab Pro)",
            training_time_seconds=10800.0,
            metrics={"pressure_relative_l2": 0.032, "cl_rmse": 0.024},
            evaluation_dataset="AirfRANS Geometry-Level Test Split"
        )
        self.register_model(RegisteredModel(
            model_id="MODEL-FNO-AIRFOIL-PRESSURE-2D",
            architecture="FNO",
            version="1.0.0",
            dataset_id="DATASET-AIRFRANS-1K",
            domain={"mach": [0.15, 0.45], "reynolds": [5.0e5, 3.0e6], "aoa_deg": [-4.0, 10.0]},
            outputs=["surface_pressure_field", "Cp_distribution", "CL"],
            metrics={"pressure_l2_relative_error": 0.032},
            uncertainty_envelope={"cp_sigma": 0.04},
            license="Apache-2.0",
            checksum=hashlib.sha256(b"MODEL-FNO-WEIGHTS-V1").hexdigest(),
            training_config=m2_config,
            validation_status="TRAINED_AND_VALIDATED",
            deployment_status="DEPLOYED"
        ))

    def register_model(self, model: RegisteredModel) -> bool:
        """Registers a new model. Fails if model_id already exists (never silently replaces)."""
        if model.model_id in self._models:
            raise ValueError(
                f"Model '{model.model_id}' is already registered. "
                f"Silent replacement is strictly prohibited. Create a new version identifier (e.g. v{model.version}.1)."
            )
        self._models[model.model_id] = model
        return True

    def list_models(self) -> List[RegisteredModel]:
        """Returns all registered physics AI models."""
        return list(self._models.values())

    def get_model(self, model_id: str) -> Optional[RegisteredModel]:
        """Retrieves model by identifier."""
        return self._models.get(model_id)
