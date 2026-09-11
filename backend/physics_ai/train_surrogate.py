"""
AASI Deterministic Pure-CPU AeroSurrogateV1 Training Script.

Executes reproducible, deterministic training on authentic airfoil data:
- Zero local GPU/CUDA requirement (runs on 4-core CPU in ~2 seconds)
- Strict random seed (seed=42) for numerical reproducibility
- Geometry-level leakage-free split
- Exports weights npz and sidecar manifest JSON with cryptographic SHA-256
- Logs training provenance: epoch trajectory, loss history, parameters
"""

import os
import sys
import json
import shutil
from pathlib import Path
from typing import Dict, Any, Optional

from backend.physics_ai.schemas import TrainingRunConfig
from backend.physics_ai.training import SurrogateTrainer


def train_and_export_surrogate(
    data_dir: str = "data/datasets/authentic_airfoils",
    output_dir: str = "data/training_runs",
    export_to_checkpoints: bool = True,
    epochs: int = 150,
    seed: int = 42,
) -> Dict[str, Any]:
    """Runs deterministic training and exports authentic checkpoint artifacts."""
    config = TrainingRunConfig(
        training_run_id="TR-AERO-SURROGATE-V1-001",
        epochs=epochs,
        batch_size=32,
        learning_rate=0.003,
        weight_decay=1e-4,
        seed=seed,
    )
    trainer = SurrogateTrainer(config=config)
    results = trainer.run_training(data_dir=data_dir, output_dir=output_dir)

    checkpoint_path = results.get("checkpoint_path")
    checksum = results.get("checksum")

    if export_to_checkpoints and checkpoint_path:
        dest_dir = Path("data/checkpoints")
        dest_dir.mkdir(parents=True, exist_ok=True)
        src_path = Path(checkpoint_path)
        dest_npz = dest_dir / "aero_surrogate_v1.npz"
        shutil.copy2(src_path, dest_npz)

        # Copy sidecar manifest if present
        src_manifest = src_path.with_suffix(".manifest.json")
        if src_manifest.exists():
            dest_manifest = dest_dir / "aero_surrogate_v1.manifest.json"
            shutil.copy2(src_manifest, dest_manifest)

        results["exported_to"] = str(dest_npz)

    return results


if __name__ == "__main__":
    print("[AASI] Initiating deterministic AeroSurrogateV1 CPU training...")
    res = train_and_export_surrogate()
    print(f"[AASI] Training complete. Checksum: {res.get('checksum')}")
    print(f"[AASI] Test R2: {res.get('test_metrics', {}).get('cl_r2', 'N/A')}")
