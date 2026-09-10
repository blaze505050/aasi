"""
AASI Open-Weight LLM Provider Abstraction.

Decouples AASI from any single hard-coded language model.
Supports local Ollama (Qwen 2.5, Llama 3, Mistral) and remote open-weight inference APIs.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import httpx
from backend.config import settings


class LLMProvider(ABC):
    """Abstract interface for open-weight language model backends."""

    @abstractmethod
    def generate(self, prompt: str, system_prompt: Optional[str] = None, max_tokens: int = 512, temperature: float = 0.2) -> str:
        """Generates response text from the underlying open-weight model."""
        pass

    @abstractmethod
    def get_model_info(self) -> Dict[str, Any]:
        """Returns metadata about the currently active model."""
        pass


class OllamaProvider(LLMProvider):
    """Default local provider connecting to Ollama runtime."""

    def __init__(self, base_url: Optional[str] = None, model_name: Optional[str] = None):
        self.base_url = base_url or settings.ollama_base_url
        self.model_name = model_name or settings.ollama_model

    def generate(self, prompt: str, system_prompt: Optional[str] = None, max_tokens: int = 512, temperature: float = 0.2) -> str:
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "system": system_prompt or settings.system_prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens
            }
        }
        try:
            with httpx.Client(timeout=30.0) as client:
                res = client.post(f"{self.base_url}/api/generate", json=payload)
                if res.status_code == 200:
                    return res.json().get("response", "")
                return f"[Ollama Error: Status {res.status_code}]"
        except Exception as e:
            return f"[Ollama Connection Error: {str(e)}]"

    def get_model_info(self) -> Dict[str, Any]:
        return {
            "provider": "Ollama (Local Open-Weight)",
            "model": self.model_name,
            "endpoint": self.base_url,
            "type": "LOCAL_OPEN_WEIGHT"
        }


class RemoteOpenWeightProvider(LLMProvider):
    """Provider for remote open-weight inference endpoints (e.g. vLLM / TGI cluster)."""

    def __init__(self, endpoint_url: str, model_name: str = "Qwen/Qwen2.5-72B-Instruct"):
        self.endpoint_url = endpoint_url
        self.model_name = model_name

    def generate(self, prompt: str, system_prompt: Optional[str] = None, max_tokens: int = 512, temperature: float = 0.2) -> str:
        # Standard OpenAI / vLLM compatible chat completions
        payload = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": system_prompt or "You are an aerospace scientific assistant."},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": max_tokens,
            "temperature": temperature
        }
        try:
            with httpx.Client(timeout=60.0) as client:
                res = client.post(f"{self.endpoint_url}/v1/chat/completions", json=payload)
                if res.status_code == 200:
                    data = res.json()
                    return data["choices"][0]["message"]["content"]
                return f"[Remote LLM Error: Status {res.status_code}]"
        except Exception as e:
            return f"[Remote LLM Connection Error: {str(e)}]"

    def get_model_info(self) -> Dict[str, Any]:
        return {
            "provider": "Remote Open-Weight Cluster (vLLM / TGI)",
            "model": self.model_name,
            "endpoint": self.endpoint_url,
            "type": "REMOTE_GPU_CLUSTER"
        }
