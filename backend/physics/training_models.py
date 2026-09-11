"""
AASI Physics-AI Training Models.

Defines training backends, training configurations, and model metadata schemas.
"""

from enum import Enum
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime, timezone


class TrainingBackendType(str, Enum):
    LOCAL = "LOCAL"            # Small smoke tests only
    COLAB = "COLAB"            # Free/Pro Google Colab GPU environment
    REMOTE_GPU = "REMOTE_GPU"  # Workstation with NVIDIA GPU
    CLOUD = "CLOUD"            # AWS / GCP / Azure compute instance
    CLUSTER = "CLUSTER"        # Slurm-managed institutional HPC


class TrainingConfig(BaseModel):
    config_id: str
    model_name: str
    architecture: str  # e.g., "AeroGraphNet", "FNO", "MeshGraphNet", "PINN"
    dataset_version: str
    hyperparameters: Dict[str, Any] = Field(default_factory=lambda: {
        "learning_rate": 1e-4,
        "batch_size": 32,
        "epochs": 100,
        "optimizer": "AdamW",
        "weight_decay": 1e-5
    })
    random_seed: int = 42
    train_split: float = 0.8
    validation_split: float = 0.1
    test_split: float = 0.1
    hardware: str = "NVIDIA A100 / Colab T4"
    software_versions: Dict[str, str] = Field(default_factory=lambda: {
        "python": "3.10+",
        "torch": "2.2+",
        "physicsnemo": "0.1.0+"
    })
    git_commit: str = "HEAD"
    training_time_seconds: Optional[float] = None
    checkpoint_path: Optional[str] = None
    metrics: Dict[str, float] = Field(default_factory=dict)
    evaluation_dataset: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class ModelLifecycleStatus(str, Enum):
    UNINITIALIZED = "UNINITIALIZED"
    TRAINING = "TRAINING"
    TRAINED_UNVERIFIED = "TRAINED_UNVERIFIED"
    VERIFIED_CHECKPOINT = "VERIFIED_CHECKPOINT"
    VERIFIED_PRODUCTION = "VERIFIED_PRODUCTION"
    FAILED = "FAILED"
    # Backward compatibility aliases
    UNTRAINED_SCAFFOLD = "UNTRAINED_SCAFFOLD"
    TRAINING_IN_PROGRESS = "TRAINING_IN_PROGRESS"
    TRAINED_LOCAL = "TRAINED_LOCAL"
    DEPRECATED = "DEPRECATED"



class TrainingProvenance(BaseModel):
    dataset_id: str
    commit_hash: Optional[str] = None
    parameter_count: int
    device_used: str = "CPU"
    epochs_trained: int
    training_duration_seconds: float
    training_timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    random_seed: int = 42
    loss_history: List[float] = Field(default_factory=list)


class RegisteredModel(BaseModel):
    model_id: str
    architecture: str
    version: str = "1.0.0"
    dataset_id: str
    domain: Dict[str, Any] = Field(default_factory=dict)  # Mach, Re, AoA validity bounds
    outputs: List[str] = Field(default_factory=lambda: ["CL", "CD", "CM"])
    metrics: Dict[str, float] = Field(default_factory=dict)
    uncertainty_envelope: Dict[str, float] = Field(default_factory=dict)
    license: str = "Apache-2.0"
    checksum: str
    training_config: TrainingConfig
    validation_status: str = "TRAINED_VALIDATED"
    deployment_status: str = "DEPLOYED"
    lifecycle_status: ModelLifecycleStatus = ModelLifecycleStatus.VERIFIED_PRODUCTION
    checkpoint_path: Optional[str] = None
    checkpoint_sha256: Optional[str] = None
    training_provenance: Optional[TrainingProvenance] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

