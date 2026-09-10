"""
AASI Training Provenance and Scientific Reproducibility Logger.

Records complete environmental context:
- Python, PyTorch, NumPy versions
- Operating System & Hardware architecture
- Git commit hash
- Dataset and split manifest cryptographic digests
- Random seeds and hyperparameter configurations.
"""

import sys
import platform
import subprocess
from datetime import datetime, timezone
from typing import Dict, Any, Optional
try:
    import torch
    HAS_TORCH = True
except Exception:
    HAS_TORCH = False
import numpy as np


class TrainingProvenanceLogger:
    """Generates immutable, auditable provenance metadata for training runs."""

    @staticmethod
    def capture_environment(
        seed: int = 42,
        dataset_checksum: str = "",
        split_checksum: str = "",
        training_config: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Captures hardware, OS, libraries, and git state."""
        # Git commit hash
        git_commit = "unknown"
        try:
            res = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if res.returncode == 0:
                git_commit = res.stdout.strip()
        except Exception:
            pass

        torch_ver = torch.__version__ if HAS_TORCH else "N/A (NumPy native CPU)"
        device_str = "cuda" if (HAS_TORCH and torch.cuda.is_available()) else "cpu"

        return {
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "git_commit": git_commit,
            "seed": seed,
            "os_name": platform.system(),
            "os_release": platform.release(),
            "python_version": sys.version.split()[0],
            "torch_version": torch_ver,
            "numpy_version": np.__version__,
            "device": device_str,
            "cpu_architecture": platform.machine(),
            "dataset_checksum": dataset_checksum,
            "split_checksum": split_checksum,
            "training_config": training_config or {},
        }

