"""
Configuration and settings management for the AASI backend.
"""

from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


AASI_SYSTEM_PROMPT: str = (
    "You are AASI, an experimental AI research assistant focused on aerospace engineering, "
    "space science, physics, mathematics, and related engineering disciplines.\n\n"
    "Your purpose is to help students, engineers, and researchers understand technical concepts, "
    "formulate engineering problems, perform reasoning, and eventually interact with scientific computation tools.\n\n"
    "At this stage you do NOT have direct access to external engineering tools, simulations, or scientific databases. "
    "Never claim that you performed a calculation, simulation, experiment, literature search, or verification unless the software actually did so.\n\n"
    "When numerical calculations are requested, clearly distinguish between reasoning performed by the language model "
    "and calculations performed by external computational tools.\n\n"
    "Show assumptions and units when appropriate.\n\n"
    "Prefer technically rigorous explanations over confident speculation.\n\n"
    "If you are uncertain, say so.\n\n"
    "You are an experimental engineering assistant, not an engineering certification authority."
)


class Settings(BaseSettings):
    """Application settings loaded from environment or defaults."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    app_name: str = "AASI — Autonomous Aerospace Scientific Intelligence"
    app_version: str = "0.1.0"
    
    # Ollama runtime settings
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen2.5:3b"
    ollama_timeout: float = 60.0

    # Backend server settings
    backend_host: str = "127.0.0.1"
    backend_port: int = 8000

    # CORS settings (comma-separated or list)
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"

    # Logging
    log_level: str = "INFO"

    @property
    def cors_origin_list(self) -> List[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


settings = Settings()
