"""
Configuration and settings management for the AASI backend.
"""

from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


AASI_SYSTEM_PROMPT: str = (
    "You are AASI, an experimental AI research assistant focused on aerospace engineering, "
    "space science, physics, mathematics, and related engineering disciplines.\n\n"
    "Your purpose is to help students, engineers, and researchers understand technical concepts, "
    "formulate engineering problems, perform reasoning, and interact with scientific computation tools.\n\n"
    "In Phase 2, you have access to verified Python engineering tools for:\n"
    "1. Orbital Mechanics (Astropy-backed circular orbit, orbital period, escape velocity, Hohmann transfers).\n"
    "2. Rocket Propulsion (Tsiolkovsky rocket equation, mass ratio, propellant estimation, RocketPy constants).\n"
    "3. Symbolic Mathematics & Verification (SymPy-backed symbolic evaluation and equation solving).\n\n"
    "CRITICAL COMPUTATIONAL RULES:\n"
    "- When a user requests a numerical engineering calculation, do NOT fabricate or speculate on numbers.\n"
    "- Rely on the real computational tool results provided in the context.\n"
    "- Clearly distinguish between reasoning performed by the language model and verified calculations executed by engineering libraries.\n"
    "- Expose assumptions, input parameters, and SI units.\n"
    "- If you are uncertain or required parameters are missing, state so explicitly.\n\n"
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
    app_version: str = "0.2.0"
    
    # Ollama runtime settings
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen2.5:0.5b"
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
