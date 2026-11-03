"""
AASI Implicit U-Net Enhanced Fourier Neural Operator (IUFNO).
Combines parameter-efficient implicit looped Fourier layers for large-scale energy modes
with symmetrical U-Net multi-scale skip connections to capture thin wall-bounded boundary layers,
leading-edge suction peaks, separated wakes, and transonic shocks on supercritical profiles.
"""

from __future__ import annotations

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Tuple, Dict, Any, List
from .fournetflows import SpectralConv2d


class ImplicitFourierLayer(nn.Module):
    """
    Implicit looping spectral layer.
    Re-uses spectral weights iteratively to evolve flow fields to fixed point,
    drastically reducing parameter count and GPU memory.
    """

    def __init__(self, channels: int, modes: int = 12, max_iterations: int = 3):
        super().__init__()
        self.channels = channels
        self.max_iterations = max_iterations
        self.spectral = SpectralConv2d(channels, channels, modes, modes)
        self.bypass = nn.Conv2d(channels, channels, kernel_size=1)
        self.norm = nn.GroupNorm(8, channels)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        h = x
        for _ in range(self.max_iterations):
            h_spec = self.spectral(h)
            h_pass = self.bypass(h)
            h = F.gelu(self.norm(h_spec + h_pass + 0.1 * x))
        return h


class UNetSkipBlock(nn.Module):
    """Multi-scale spatial encoder-decoder block preserving fine-scale boundary layer gradients."""

    def __init__(self, in_c: int, out_c: int):
        super().__init__()
        self.conv1 = nn.Conv2d(in_c, out_c, kernel_size=3, padding=1)
        self.conv2 = nn.Conv2d(out_c, out_c, kernel_size=3, padding=1)
        self.norm = nn.GroupNorm(8, out_c)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        h = F.gelu(self.conv1(x))
        h = F.gelu(self.norm(self.conv2(h)))
        return h


class IUFNOModel(nn.Module):
    """
    Implicit U-Net FNO:
    1. Multiscale U-Net Encoder: captures fine near-wall boundary layer eddies
    2. Deep Latent Implicit Spectral Core: resolves global infinite-dimensional solution operator
    3. Multiscale U-Net Decoder with Skip Connections: reconstructs sharp shocks and suction peaks
    """

    def __init__(
        self,
        in_channels: int = 5,  # [x, y, mask, alpha, Re]
        out_channels: int = 3,  # [u, v, p]
        base_channels: int = 48,
        modes: int = 12,
        implicit_loops: int = 3,
    ):
        super().__init__()
        self.in_channels = in_channels
        self.out_channels = out_channels

        # Encoder (Multi-scale downsampling)
        self.enc1 = UNetSkipBlock(in_channels, base_channels)
        self.pool1 = nn.MaxPool2d(2)

        self.enc2 = UNetSkipBlock(base_channels, base_channels * 2)
        self.pool2 = nn.MaxPool2d(2)

        # Bottleneck: Implicit Fourier Neural Operator Core
        self.bottleneck_channels = base_channels * 2
        self.implicit_spectral = ImplicitFourierLayer(
            self.bottleneck_channels, modes=modes, max_iterations=implicit_loops
        )

        # Decoder (Multi-scale upsampling + Skip Connections)
        self.up2 = nn.ConvTranspose2d(base_channels * 2, base_channels, kernel_size=2, stride=2)
        self.dec2 = UNetSkipBlock(base_channels * 2, base_channels)

        self.up1 = nn.ConvTranspose2d(base_channels, base_channels, kernel_size=2, stride=2)
        self.dec1 = UNetSkipBlock(base_channels + base_channels, base_channels)

        # Final projection to (u, v, p)
        self.final_conv = nn.Conv2d(base_channels, out_channels, kernel_size=1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        x: [B, in_channels, H, W]
        Returns: [B, out_channels, H, W]
        """
        # 1. Encoder
        e1 = self.enc1(x)  # [B, C, H, W]
        p1 = self.pool1(e1)  # [B, C, H/2, W/2]

        e2 = self.enc2(p1)  # [B, 2C, H/2, W/2]
        p2 = self.pool2(e2)  # [B, 2C, H/4, W/4]

        # 2. Implicit Spectral Bottleneck
        b = self.implicit_spectral(p2)  # [B, 2C, H/4, W/4]

        # 3. Decoder with Skip Connections
        u2 = self.up2(b)  # [B, C, H/2, W/2]
        d2 = self.dec2(torch.cat([u2, p1], dim=1))  # [B, C, H/2, W/2]

        u1 = self.up1(d2)  # [B, C, H, W]
        d1 = self.dec1(torch.cat([u1, e1], dim=1))  # [B, C, H, W]

        # 4. Final output
        out = self.final_conv(d1)
        return out

