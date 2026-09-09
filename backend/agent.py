"""
AASI Agent Layer: Orchestration between user queries, system prompt, and Ollama runtime.
"""

import logging
from typing import Any, Dict, Optional, Tuple
import httpx

from backend.config import AASI_SYSTEM_PROMPT, settings

logger = logging.getLogger(__name__)


class AASIAgentError(Exception):
    """Base exception for AASI Agent errors."""
    pass


class OllamaUnavailableError(AASIAgentError):
    """Raised when the Ollama runtime is unreachable."""
    pass


class OllamaRuntimeError(AASIAgentError):
    """Raised when Ollama returns an error or fails during inference."""
    pass


class AASIAgent:
    """Orchestrates AI reasoning and communication with the open-weight LLM on Ollama."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        timeout: Optional[float] = None,
        system_prompt: Optional[str] = None,
    ):
        self.base_url = (base_url or settings.ollama_base_url).rstrip("/")
        self.model = model or settings.ollama_model
        self.timeout = timeout or settings.ollama_timeout
        self.system_prompt = system_prompt or AASI_SYSTEM_PROMPT

    async def check_health(self) -> Tuple[bool, Optional[str]]:
        """
        Check if Ollama runtime is reachable and responsive.
        Returns a tuple of (is_healthy, status_or_error_message).
        """
        url = f"{self.base_url}/api/tags"
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(url)
                if response.status_code == 200:
                    data = response.json()
                    models = [m.get("name") for m in data.get("models", []) if "name" in m]
                    logger.debug("Ollama is reachable. Available models: %s", models)
                    return True, None
                else:
                    return False, f"Ollama returned HTTP status {response.status_code}"
        except httpx.ConnectError:
            return False, f"Could not connect to Ollama at {self.base_url}. Ensure Ollama is running."
        except httpx.TimeoutException:
            return False, f"Connection to Ollama timed out at {self.base_url}."
        except Exception as exc:
            return False, f"Unexpected error connecting to Ollama: {str(exc)}"

    async def generate_response(self, user_message: str) -> Dict[str, Any]:
        """
        Send user message with AASI system prompt to Ollama and return structured response.
        """
        if not user_message or not user_message.strip():
            raise ValueError("User message cannot be empty.")

        url = f"{self.base_url}/api/chat"
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": self.system_prompt,
                },
                {
                    "role": "user",
                    "content": user_message.strip(),
                },
            ],
            "stream": False,
        }

        logger.info("Dispatching prompt to Ollama model '%s' at %s", self.model, url)

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, json=payload)
        except httpx.ConnectError as exc:
            logger.error("Connection error while communicating with Ollama: %s", exc)
            raise OllamaUnavailableError(
                f"Cannot connect to Ollama at {self.base_url}. Please verify that the Ollama service is running "
                f"and accessible."
            ) from exc
        except httpx.TimeoutException as exc:
            logger.error("Timeout waiting for Ollama response: %s", exc)
            raise OllamaRuntimeError(
                f"Ollama timed out after {self.timeout}s waiting for model '{self.model}'."
            ) from exc
        except Exception as exc:
            logger.error("Unexpected network error while contacting Ollama: %s", exc)
            raise OllamaRuntimeError(f"Network error communicating with Ollama: {str(exc)}") from exc

        if response.status_code != 200:
            error_detail = response.text
            logger.error("Ollama returned error HTTP %d: %s", response.status_code, error_detail)
            if response.status_code == 404:
                raise OllamaRuntimeError(
                    f"Model '{self.model}' was not found in Ollama. "
                    f"Run `ollama pull {self.model}` to download it or change OLLAMA_MODEL."
                )
            raise OllamaRuntimeError(f"Ollama error (HTTP {response.status_code}): {error_detail}")

        try:
            data = response.json()
            model_response = data.get("message", {}).get("content", "")
            actual_model = data.get("model", self.model)
            return {
                "response": model_response,
                "model": actual_model,
                "status": "success",
            }
        except Exception as exc:
            logger.error("Failed to parse Ollama response JSON: %s", exc)
            raise OllamaRuntimeError(f"Failed to parse Ollama JSON response: {str(exc)}") from exc


# Default module-level agent instance
default_agent = AASIAgent()
