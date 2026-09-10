"""
AASI First Real Physics-AI Model: AeroSurrogateV1.

Implements a lightweight, deterministic neural operator mapping
Airfoil Geometry Coordinates + Flow Conditions (Mach, Re, AoA) -> [CL, CD, CM].
Uses a split Geometry Encoder + Condition Encoder + Fusion Network architecture
with residual skip connections and AdamW optimization.
Fully self-contained in vectorized NumPy for 100% platform portability and zero-DLL dependency.
"""

import json
import hashlib
from typing import Dict, Any, Tuple, Optional, List
import numpy as np


def gelu(x: np.ndarray) -> np.ndarray:
    """Gaussian Error Linear Unit activation."""
    return 0.5 * x * (1.0 + np.tanh(np.sqrt(2.0 / np.pi) * (x + 0.044715 * (x ** 3))))


def gelu_derivative(x: np.ndarray) -> np.ndarray:
    """Derivative of GELU for backpropagation."""
    s = np.sqrt(2.0 / np.pi)
    t = np.tanh(s * (x + 0.044715 * (x ** 3)))
    sech2 = 1.0 - t ** 2
    return 0.5 * (1.0 + t) + 0.5 * x * sech2 * s * (1.0 + 3.0 * 0.044715 * (x ** 2))


class AeroSurrogateV1:
    """
    Production-quality lightweight neural surrogate for aerodynamic coefficients.
    Maps: Airfoil Geometry + [Mach, Reynolds, AoA] -> [CL, CD, CM].
    """

    def __init__(
        self,
        coords_points: int = 64,
        geom_latent_dim: int = 32,
        cond_latent_dim: int = 16,
        hidden_dim: int = 64,
        seed: int = 42
    ):
        self.coords_points = coords_points
        self.geom_in_dim = coords_points * 2
        self.geom_latent_dim = geom_latent_dim
        self.cond_in_dim = 3
        self.cond_latent_dim = cond_latent_dim
        self.hidden_dim = hidden_dim
        self.out_dim = 3  # [CL, CD, CM]

        self.model_id = "AERO_SURROGATE_V1"
        self.model_version = "1.0.0"
        self.seed = seed

        self.params: Dict[str, np.ndarray] = {}
        self._init_weights(seed)

    def _init_weights(self, seed: int):
        rng = np.random.RandomState(seed)

        def xavier(din: int, dout: int) -> np.ndarray:
            scale = np.sqrt(2.0 / (din + dout))
            return (rng.randn(din, dout) * scale).astype(np.float32)

        def zeros(dout: int) -> np.ndarray:
            return np.zeros(dout, dtype=np.float32)

        # Geometry Encoder: 128 -> 64 -> 32
        self.params["Wg1"] = xavier(self.geom_in_dim, 64)
        self.params["bg1"] = zeros(64)
        self.params["Wg2"] = xavier(64, self.geom_latent_dim)
        self.params["bg2"] = zeros(self.geom_latent_dim)

        # Condition Encoder: 3 -> 32 -> 16
        self.params["Wc1"] = xavier(self.cond_in_dim, 32)
        self.params["bc1"] = zeros(32)
        self.params["Wc2"] = xavier(32, self.cond_latent_dim)
        self.params["bc2"] = zeros(self.cond_latent_dim)

        # Fusion: 48 -> 64 -> 64 (res) -> 32 -> 3
        fusion_in = self.geom_latent_dim + self.cond_latent_dim
        self.params["Wf1"] = xavier(fusion_in, self.hidden_dim)
        self.params["bf1"] = zeros(self.hidden_dim)
        self.params["Wf2"] = xavier(self.hidden_dim, self.hidden_dim)
        self.params["bf2"] = zeros(self.hidden_dim)
        self.params["Wf3"] = xavier(self.hidden_dim, 32)
        self.params["bf3"] = zeros(32)
        self.params["Wout"] = xavier(32, self.out_dim)
        self.params["bout"] = zeros(self.out_dim)

    def forward(
        self,
        geom_coords: np.ndarray,
        conditions: np.ndarray,
        return_intermediates: bool = False
    ) -> np.ndarray:
        """
        Forward pass.
        geom_coords: [B, 64, 2] or [B, 128]
        conditions:  [B, 3]
        returns:     [B, 3] normalized [CL, CD, CM]
        """
        B = geom_coords.shape[0]
        X_geom = geom_coords.reshape(B, -1)
        X_cond = conditions.reshape(B, -1)

        # Geometry Encoder
        z_g1 = np.dot(X_geom, self.params["Wg1"]) + self.params["bg1"]
        h_g1 = gelu(z_g1)
        h_geom = np.dot(h_g1, self.params["Wg2"]) + self.params["bg2"]

        # Condition Encoder
        z_c1 = np.dot(X_cond, self.params["Wc1"]) + self.params["bc1"]
        h_c1 = gelu(z_c1)
        h_cond = np.dot(h_c1, self.params["Wc2"]) + self.params["bc2"]

        # Fusion
        fused = np.concatenate([h_geom, h_cond], axis=-1)
        z_f1 = np.dot(fused, self.params["Wf1"]) + self.params["bf1"]
        h_f1 = gelu(z_f1)

        z_f2 = np.dot(h_f1, self.params["Wf2"]) + self.params["bf2"]
        h_f2 = gelu(z_f2) + h_f1  # Residual connection

        z_f3 = np.dot(h_f2, self.params["Wf3"]) + self.params["bf3"]
        h_f3 = gelu(z_f3)

        out = np.dot(h_f3, self.params["Wout"]) + self.params["bout"]

        if return_intermediates:
            cache = {
                "X_geom": X_geom, "X_cond": X_cond,
                "z_g1": z_g1, "h_g1": h_g1, "h_geom": h_geom,
                "z_c1": z_c1, "h_c1": h_c1, "h_cond": h_cond,
                "fused": fused, "z_f1": z_f1, "h_f1": h_f1,
                "z_f2": z_f2, "h_f2": h_f2, "z_f3": z_f3, "h_f3": h_f3,
                "out": out
            }
            return out, cache

        return out

    def backward(self, d_loss_dout: np.ndarray, cache: Dict[str, np.ndarray]) -> Dict[str, np.ndarray]:
        """Backpropagation to compute analytical gradients for all weights."""
        grads: Dict[str, np.ndarray] = {}
        B = d_loss_dout.shape[0]

        # Output layer
        grads["Wout"] = np.dot(cache["h_f3"].T, d_loss_dout) / B
        grads["bout"] = np.sum(d_loss_dout, axis=0) / B

        d_h_f3 = np.dot(d_loss_dout, self.params["Wout"].T)
        d_z_f3 = d_h_f3 * gelu_derivative(cache["z_f3"])

        grads["Wf3"] = np.dot(cache["h_f2"].T, d_z_f3) / B
        grads["bf3"] = np.sum(d_z_f3, axis=0) / B

        d_h_f2 = np.dot(d_z_f3, self.params["Wf3"].T)
        # Residual skip derivative
        d_z_f2 = d_h_f2 * gelu_derivative(cache["z_f2"])
        grads["Wf2"] = np.dot(cache["h_f1"].T, d_z_f2) / B
        grads["bf2"] = np.sum(d_z_f2, axis=0) / B

        d_h_f1 = np.dot(d_z_f2, self.params["Wf2"].T) + d_h_f2
        d_z_f1 = d_h_f1 * gelu_derivative(cache["z_f1"])

        grads["Wf1"] = np.dot(cache["fused"].T, d_z_f1) / B
        grads["bf1"] = np.sum(d_z_f1, axis=0) / B

        d_fused = np.dot(d_z_f1, self.params["Wf1"].T)
        d_h_geom = d_fused[:, :self.geom_latent_dim]
        d_h_cond = d_fused[:, self.geom_latent_dim:]

        # Condition encoder
        grads["Wc2"] = np.dot(cache["h_c1"].T, d_h_cond) / B
        grads["bc2"] = np.sum(d_h_cond, axis=0) / B

        d_h_c1 = np.dot(d_h_cond, self.params["Wc2"].T)
        d_z_c1 = d_h_c1 * gelu_derivative(cache["z_c1"])
        grads["Wc1"] = np.dot(cache["X_cond"].T, d_z_c1) / B
        grads["bc1"] = np.sum(d_z_c1, axis=0) / B

        # Geometry encoder
        grads["Wg2"] = np.dot(cache["h_g1"].T, d_h_geom) / B
        grads["bg2"] = np.sum(d_h_geom, axis=0) / B

        d_h_g1 = np.dot(d_h_geom, self.params["Wg2"].T)
        d_z_g1 = d_h_g1 * gelu_derivative(cache["z_g1"])
        grads["Wg1"] = np.dot(cache["X_geom"].T, d_z_g1) / B
        grads["bg1"] = np.sum(d_z_g1, axis=0) / B

        return grads

    def count_parameters(self) -> int:
        """Returns total trainable parameter count."""
        return sum(p.size for p in self.params.values())

    def compute_weights_checksum(self) -> str:
        """Deterministic SHA-256 hash of all parameters."""
        hasher = hashlib.sha256()
        for name in sorted(self.params.keys()):
            hasher.update(name.encode())
            hasher.update(self.params[name].astype(np.float32).tobytes())
        return hasher.hexdigest()

    def state_dict(self) -> Dict[str, Any]:
        """Exports weights dictionary."""
        return {k: v.tolist() for k, v in self.params.items()}

    def load_state_dict(self, state: Dict[str, Any]):
        """Imports weights dictionary."""
        for k, v in state.items():
            if k in self.params:
                self.params[k] = np.array(v, dtype=np.float32)
