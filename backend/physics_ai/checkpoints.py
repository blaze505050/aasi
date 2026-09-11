"""
AASI Checkpoint Management and Weight Integrity.

Saves and loads versioned surrogate models with cryptographic checksums,
normalizer states, and training metadata using portable, zero-DLL NumPy archive format.
"""

import json
import hashlib
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import numpy as np

from backend.physics_ai.models import AeroSurrogateV1
from backend.physics_ai.normalization import FlowConditionNormalizer, AerodynamicTargetScaler


class CheckpointManager:
    """Manages serializing and loading trained models with cryptographic verification."""

    def __init__(self, checkpoints_dir: str = "data/checkpoints"):
        self.checkpoints_dir = Path(checkpoints_dir)
        self.checkpoints_dir.mkdir(parents=True, exist_ok=True)

    def save_checkpoint(
        self,
        model: AeroSurrogateV1,
        condition_normalizer: FlowConditionNormalizer,
        target_scaler: AerodynamicTargetScaler,
        training_metadata: Dict[str, Any],
        filename: str = "aero_surrogate_v1.npz"
    ) -> Tuple[Path, str]:
        """Saves model weights as compressed npz, exports normalizers, and computes SHA-256 checksum."""
        if not filename.endswith(".npz"):
            filename = filename.rsplit(".", 1)[0] + ".npz"
        target_path = self.checkpoints_dir / filename

        # Save model parameters
        np.savez_compressed(target_path, **model.params)

        # Compute file checksum
        hasher = hashlib.sha256()
        with open(target_path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                hasher.update(chunk)
        checksum = hasher.hexdigest()

        # Write accompanying sidecar JSON with normalizers and provenance
        sidecar_path = target_path.with_suffix(".manifest.json")
        manifest_data = {
            "model_id": model.model_id,
            "model_version": model.model_version,
            "checkpoint_file": target_path.name,
            "sha256_checksum": checksum,
            "parameter_count": model.count_parameters(),
            "condition_normalizer": condition_normalizer.to_dict(),
            "target_scaler": target_scaler.to_dict(),
            "training_metadata": training_metadata,
        }
        sidecar_path.write_text(json.dumps(manifest_data, indent=2), encoding="utf-8")

        return target_path, checksum

    def load_checkpoint(
        self,
        checkpoint_path: Path
    ) -> Tuple[AeroSurrogateV1, FlowConditionNormalizer, AerodynamicTargetScaler, Dict[str, Any], str]:
        """Loads model weights, normalizers, and verifies checksum."""
        checkpoint_path = Path(checkpoint_path)
        if not checkpoint_path.exists():
            # Check if .npz variant exists
            npz_candidate = checkpoint_path.with_suffix(".npz")
            if npz_candidate.exists():
                checkpoint_path = npz_candidate
            else:
                raise FileNotFoundError(f"Checkpoint not found at '{checkpoint_path}'.")

        # Verify checksum if manifest exists
        sidecar = checkpoint_path.with_suffix(".manifest.json")
        expected_checksum = None
        manifest_data = {}
        if sidecar.exists():
            manifest_data = json.loads(sidecar.read_text(encoding="utf-8"))
            expected_checksum = manifest_data.get("sha256_checksum")

        hasher = hashlib.sha256()
        with open(checkpoint_path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                hasher.update(chunk)
        actual_checksum = hasher.hexdigest()

        if expected_checksum and actual_checksum != expected_checksum:
            raise ValueError(f"Checksum mismatch for '{checkpoint_path}': expected {expected_checksum}, got {actual_checksum}")

        # Load weights
        npz_data = np.load(checkpoint_path)
        state_dict = {k: npz_data[k] for k in npz_data.files}

        model = AeroSurrogateV1()
        model.load_state_dict(state_dict)

        norm = FlowConditionNormalizer.from_dict(manifest_data.get("condition_normalizer", {}))
        scaler = AerodynamicTargetScaler.from_dict(manifest_data.get("target_scaler", {}))
        metadata = manifest_data.get("training_metadata", {})

        return model, norm, scaler, metadata, actual_checksum

    @staticmethod
    def verify_checkpoint_integrity(
        checkpoint_path: Path, expected_sha256: Optional[str] = None
    ) -> Tuple[bool, str, str]:
        """Checks if checkpoint exists, computes SHA-256, and compares with expected value.
        
        Returns (is_valid, actual_sha256, status_message).
        """
        checkpoint_path = Path(checkpoint_path)
        if not checkpoint_path.exists():
            return False, "", f"Checkpoint file '{checkpoint_path}' does not exist."

        hasher = hashlib.sha256()
        with open(checkpoint_path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                hasher.update(chunk)
        actual_sha256 = hasher.hexdigest()

        if expected_sha256:
            if actual_sha256 != expected_sha256:
                return False, actual_sha256, f"Checksum mismatch: expected {expected_sha256}, got {actual_sha256}"
            return True, actual_sha256, "Verified authentic checkpoint matching registered checksum."

        return True, actual_sha256, "Checkpoint file verified on disk."

