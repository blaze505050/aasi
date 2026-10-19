"""
AASI Phase 27: Production Deployment & Zero-Cost Configuration.
Governing Doctrine: Absolute Anti-Fabrication Rule.
Ensures zero-cost operation when needed while strictly forbidding synthetic result masquerading.
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
import os
from pathlib import Path


class DeploymentConfig(BaseModel):
    """
    Platform deployment configuration.
    Controls environment modes, compute provider availability, and resource quotas.
    """
    environment: str = Field(default_factory=lambda: os.getenv("AASI_ENV", "production"))
    dev_mode: bool = Field(default_factory=lambda: os.getenv("AASI_DEV_MODE", "false").lower() in ("true", "1", "yes"))
    api_prefix: str = "/api"
    secret_key: str = Field(default_factory=lambda: os.getenv("AASI_SECRET_KEY", "aasi-dev-key-CHANGE-IN-PRODUCTION"))
    token_expiry_hours: int = 24
    
    # Storage configuration
    storage_backend: str = Field(default_factory=lambda: os.getenv("AASI_STORAGE_BACKEND", "local"))
    storage_base_dir: str = Field(default_factory=lambda: os.getenv("AASI_STORAGE_DIR", "data/storage"))
    s3_bucket: Optional[str] = Field(default_factory=lambda: os.getenv("AASI_S3_BUCKET", None))
    s3_endpoint_url: Optional[str] = Field(default_factory=lambda: os.getenv("AASI_S3_ENDPOINT", None))
    
    # Resource Quotas & Governance
    max_concurrent_jobs_per_user: int = 2
    max_archive_size_bytes: int = 100 * 1024 * 1024  # 100 MB
    max_cfd_runtime_seconds: int = 1800  # 30 minutes
    max_mesh_cells: int = 500_000
    max_retries: int = 3
    rate_limit_per_minute: int = 60
    
    # Provider availability
    enable_colab_provider: bool = True
    enable_local_openfoam: bool = False  # Keep false by default to prevent laptop CPU load
    enable_remote_hpc: bool = True
    
    # Absolute Anti-Fabrication Rule
    forbid_synthetic_substitution: bool = True
    stage_10_gate_enforced: bool = True
    cors_origins: List[str] = Field(default_factory=lambda: [
        o.strip() for o in os.getenv("AASI_CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000").split(",") if o.strip()
    ])

    # Phase 27 Aliases
    zero_cost_mode: bool = True
    allow_synthetic_fallback: bool = False
    max_archive_mb: int = 500
    max_execution_timeout_sec: int = 3600

    def validate_production_readiness(self) -> Dict[str, Any]:
        """
        Validates whether the current deployment configuration satisfies
        all production security and operational requirements.
        Returns a dictionary of audited items categorized as READY, BLOCKED, or REQUIRES_CONFIGURATION.
        """
        audit = {
            "environment_mode": "READY",
            "secret_key": "READY",
            "cors_origins": "READY",
            "auth_enforcement": "READY",
            "storage_persistence": "READY",
            "anti_fabrication": "READY",
            "blockers": [],
            "warnings": [],
        }

        # 1. Dev mode cannot be enabled in production
        is_prod = self.environment.lower() == "production"
        if is_prod and self.dev_mode:
            audit["environment_mode"] = "BLOCKED"
            audit["blockers"].append("CRITICAL: AASI_DEV_MODE cannot be enabled in production (AASI_ENV=production).")

        # 2. Secret key cannot use default development placeholder in production
        DEFAULT_PLACEHOLDERS = [
            "aasi-dev-key-CHANGE-IN-PRODUCTION",
            "aasi-secret-key-phase27-production-secure",
            "aasi-production-key-change-in-prod",
            "secret",
            "changeme",
            "change-this-to-a-cryptographically-secure-random-64-char-token",
        ]
        if is_prod and self.secret_key in DEFAULT_PLACEHOLDERS:
            audit["secret_key"] = "BLOCKED"
            audit["blockers"].append(
                "CRITICAL: AASI_SECRET_KEY is using a default placeholder. "
                "Generate a secure key: python -c \"import secrets; print(secrets.token_hex(32))\""
            )
        elif is_prod and len(self.secret_key) < 32:
            audit["secret_key"] = "REQUIRES_CONFIGURATION"
            audit["warnings"].append(
                "AASI_SECRET_KEY is shorter than 32 characters. Use a minimum 32-byte random hex string."
            )

        # 3. CORS origins should not allow wildcard '*' in production
        if is_prod and "*" in self.cors_origins:
            audit["cors_origins"] = "REQUIRES_CONFIGURATION"
            audit["warnings"].append("CORS origins allows wildcard '*'. Restrict to specific trusted domains (e.g. https://aasi.projectpolaris.in).")

        # 4. Storage persistence
        storage_path = Path(self.storage_base_dir)
        if not storage_path.exists():
            try:
                storage_path.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                audit["storage_persistence"] = "BLOCKED"
                audit["blockers"].append(f"Storage directory {self.storage_base_dir} cannot be created: {e}")

        # 5. Anti-Fabrication & Epistemic Gate
        if not self.forbid_synthetic_substitution or not self.stage_10_gate_enforced:
            audit["anti_fabrication"] = "BLOCKED"
            audit["blockers"].append("CRITICAL: Anti-fabrication rules or Stage-10 gate are disabled.")

        audit["is_launch_ready"] = len(audit["blockers"]) == 0
        return audit


# Global singleton instance
deployment_config = DeploymentConfig()


def get_deployment_config() -> DeploymentConfig:
    """Retrieve global deployment configuration."""
    return deployment_config
