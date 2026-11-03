"""
AASI Geometry-Aware Fourier Neural Operator (Geo-FNO).
Maps irregular body-fitted computational domains (e.g. 221x51 C-grids, NACA profiles)
into a uniform latent unit cube via learned coordinate deformation.
Executes native FFT spectral convolutions and computes exact chain-rule PDE derivatives.
"""

from __future__ import annotations

import math
import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Dict, Any, Tuple, Optional
from .fournetflows import SpectralConv2d


class MeshDeformationNetwork(nn.Module):
    """
    Learns continuous deformation phi: (x, y) -> (xi, eta)
    mapping irregular physical domains into uniform latent space [0, 1]^2.
    """

    def __init__(self, hidden_dim: int = 64):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(2, hidden_dim),
            nn.Tanh(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.Tanh(),
            nn.Linear(hidden_dim, 2),
            nn.Sigmoid(),  # Bound to [0, 1]
        )

    def forward(self, xy: torch.Tensor) -> torch.Tensor:
        """
        xy: [..., 2] coordinates in physical domain
        Returns: [..., 2] coordinates in latent domain [0, 1]^2
        """
        return self.net(xy)

    def compute_jacobian(self, xy: torch.Tensor) -> torch.Tensor:
        """Computes 2x2 Jacobian matrix d(xi, eta)/d(x, y) using PyTorch autograd."""
        xy_req = xy.clone().detach().requires_grad_(True)
        latent = self.forward(xy_req)
        # Compute gradients for each component
        d_xi = torch.autograd.grad(latent[..., 0].sum(), xy_req, create_graph=True)[0]
        d_eta = torch.autograd.grad(latent[..., 1].sum(), xy_req, create_graph=True)[0]
        jacobian = torch.stack([d_xi, d_eta], dim=-1)  # [..., 2, 2]
        return jacobian


class GeoFNOAirfoilModel(nn.Module):
    """
    Geo-FNO for aerodynamic meshes:
    1. Coordinate deformation: physical (x, y) -> latent (xi, eta)
    2. Interpolate irregular mesh features onto regular (H, W) latent grid
    3. Spectral Fourier convolutions in latent domain
    4. Push back to irregular mesh stations
    """

    def __init__(
        self,
        in_channels: int = 4,  # [x, y, alpha, Mach]
        out_channels: int = 3,  # [u, v, p]
        latent_res: Tuple[int, int] = (64, 64),
        hidden_dim: int = 96,
        modes: int = 12,
        num_layers: int = 4,
    ):
        super().__init__()
        self.latent_H, self.latent_W = latent_res
        self.hidden_dim = hidden_dim

        self.deformation_net = MeshDeformationNetwork(hidden_dim=hidden_dim)

        # Latent grid lifting
        self.lifting = nn.Linear(in_channels + 2, hidden_dim)  # includes (xi, eta)

        # Spectral convolution stack in latent space
        self.spectral_layers = nn.ModuleList([
            SpectralConv2d(hidden_dim, hidden_dim, modes, modes)
            for _ in range(num_layers)
        ])
        self.bypass_convs = nn.ModuleList([
            nn.Conv2d(hidden_dim, hidden_dim, kernel_size=1)
            for _ in range(num_layers)
        ])

        # Projection back to field quantities
        self.projection = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.GELU(),
            nn.Linear(hidden_dim // 2, out_channels),
        )

    def forward(
        self,
        physical_coords: torch.Tensor,
        physical_features: torch.Tensor,
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        physical_coords: [B, N_points, 2] (x, y)
        physical_features: [B, N_points, in_channels] (e.g. freestream alpha, Mach)
        Returns:
            pred_fields: [B, N_points, out_channels] (u, v, p)
            latent_coords: [B, N_points, 2] (xi, eta)
        """
        B, N, _ = physical_coords.shape

        # 1. Deform to latent coordinates
        latent_coords = self.deformation_net(physical_coords)  # [B, N, 2] in [0, 1]^2

        # 2. Combine physical features with latent coordinates
        lifted_input = torch.cat([physical_features, latent_coords], dim=-1)
        h_nodes = self.lifting(lifted_input)  # [B, N, hidden_dim]

        # 3. Discretize into regular 2D latent grid via grid scatter / bilinear splat
        grid_h = torch.zeros(
            B, self.hidden_dim, self.latent_H, self.latent_W, device=physical_coords.device
        )

        xi = (latent_coords[..., 0] * (self.latent_W - 1)).clamp(0, self.latent_W - 1).long()
        eta = (latent_coords[..., 1] * (self.latent_H - 1)).clamp(0, self.latent_H - 1).long()

        for b in range(B):
            grid_h[b, :, eta[b], xi[b]] = h_nodes[b].transpose(0, 1)

        # 4. Spectral Fourier convolutions in latent domain
        h = grid_h
        for spec, bypass in zip(self.spectral_layers, self.bypass_convs):
            h = F.gelu(spec(h) + bypass(h))

        # 5. Interpolate back to original irregular mesh points
        # Sample grid_h at (xi, eta)
        norm_grid_coords = 2.0 * latent_coords.unsqueeze(2) - 1.0  # [B, N, 1, 2] in [-1, 1]
        sampled_h = F.grid_sample(
            h, norm_grid_coords, mode="bilinear", padding_mode="border", align_corners=True
        )  # [B, hidden_dim, N, 1]
        sampled_h = sampled_h.squeeze(-1).transpose(1, 2)  # [B, N, hidden_dim]

        # 6. Final projection to output flow quantities
        out_fields = self.projection(sampled_h)  # [B, N, out_channels]
        return out_fields, latent_coords

