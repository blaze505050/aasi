"""
AASI Phase 27: Compute Provider Manager.
Central registry and capability coordinator for compute backends.
Decouples the scientific discovery agent from specific execution hardware.
"""

from typing import Dict, List, Optional, Any
from backend.compute.base import ComputeProvider, ProviderCapability
from backend.compute.providers.local_openfoam import LocalOpenFOAMProvider
from backend.compute.providers.colab_provider import ColabProvider
from backend.compute.providers.remote_hpc import RemoteHPCProvider
from backend.deployment.config import get_deployment_config


class ComputeProviderManager:
    """Manages available compute backends, probes capabilities, and routes jobs."""

    def __init__(self):
        self.config = get_deployment_config()
        self._providers: Dict[str, ComputeProvider] = {
            "LOCAL_OPENFOAM": LocalOpenFOAMProvider(),
            "COLAB": ColabProvider(),
            "REMOTE_HPC": RemoteHPCProvider(),
        }

    def register_provider(self, provider_or_name: Any, provider: Optional[ComputeProvider] = None):
        if provider is not None:
            self._providers[str(provider_or_name).upper()] = provider
        elif hasattr(provider_or_name, "name"):
            self._providers[provider_or_name.name.upper()] = provider_or_name
        else:
            self._providers[str(provider_or_name).upper()] = provider_or_name

    def list_providers(self) -> List[Any]:
        return list(self._providers.values())

    def select_provider(self, preference: Optional[str] = None) -> ComputeProvider:
        return self.select_optimal_provider(preference)

    def get_provider(self, name: str) -> ComputeProvider:
        key = name.upper()
        if key not in self._providers:
            # Fallback to Colab
            return self._providers["COLAB"]
        return self._providers[key]

    def probe_all(self) -> Dict[str, ProviderCapability]:
        """Probe all registered providers and return capabilities."""
        capabilities = {}
        for name, provider in self._providers.items():
            capabilities[name] = provider.probe()
        return capabilities

    def select_optimal_provider(self, preference: Optional[str] = None) -> ComputeProvider:
        """
        Route to best available backend.
        Preference order: Requested backend -> COLAB (zero-cost cloud) -> REMOTE_HPC -> LOCAL.
        """
        if preference and preference.upper() in self._providers:
            cand = self._providers[preference.upper()]
            probe = cand.probe()
            if probe.available:
                return cand

        # Default recommendation: Colab for zero-cost remote execution
        colab = self._providers["COLAB"]
        if colab.probe().available:
            return colab

        # Remote HPC
        hpc = self._providers["REMOTE_HPC"]
        if hpc.probe().available:
            return hpc

        # Fallback to Local OpenFOAM
        return self._providers["LOCAL_OPENFOAM"]


ProviderManager = ComputeProviderManager



# Global singleton provider manager
provider_manager = ComputeProviderManager()
