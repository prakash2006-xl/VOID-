#!/usr/bin/env python3
"""
VOID Agentic OS — Local and Optional Cloud AI Provider Layer
Default: Local Ollama (100% offline, zero cloud reliance).
Optional: User-configured cloud providers with secret masking and privacy guards.
"""

from __future__ import annotations
import json
import os
import time
from pathlib import Path
from abc import ABC, abstractmethod
from typing import Any, Optional
import httpx

# Default Local Endpoint
DEFAULT_OLLAMA_URL = os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434")
DEFAULT_LOCAL_MODEL = "lfm3-omni:2b"

class BaseAIProvider(ABC):
    name: str = "base"
    is_local: bool = True

    @abstractmethod
    def generate(self, prompt: str, system: str = "", temperature: float = 0.3, max_tokens: int = 1024) -> str:
        """Generates completion text."""
        pass

    @abstractmethod
    def test_connection(self) -> dict[str, Any]:
        """Tests provider availability and health."""
        pass

class LocalOllamaProvider(BaseAIProvider):
    """Local Ollama Inference Provider (Offline, Keyless)."""
    name = "ollama-local"
    is_local = True

    def __init__(self, base_url: str = DEFAULT_OLLAMA_URL, model: str = DEFAULT_LOCAL_MODEL) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model

    def generate(self, prompt: str, system: str = "", temperature: float = 0.3, max_tokens: int = 1024) -> str:
        url = f"{self.base_url}/api/generate"
        payload = {
            "model": self.model,
            "prompt": prompt,
            "system": system,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens
            }
        }
        try:
            r = httpx.post(url, json=payload, timeout=45.0)
            if r.status_code == 200:
                data = r.json()
                return data.get("response", "").strip()
            raise RuntimeError(f"Ollama returned HTTP {r.status_code}: {r.text[:200]}")
        except Exception as e:
            raise RuntimeError(f"Local Ollama generation error: {e}") from e

    def test_connection(self) -> dict[str, Any]:
        t0 = time.time()
        try:
            r = httpx.get(f"{self.base_url}/api/tags", timeout=3.0)
            lat = round((time.time() - t0) * 1000, 1)
            if r.status_code == 200:
                models = [m.get("name", "") for m in r.json().get("models", [])]
                has_target = any(self.model in m for m in models)
                return {
                    "online": True,
                    "latency_ms": lat,
                    "provider": self.name,
                    "model": self.model,
                    "installed_models": models,
                    "target_model_ready": has_target
                }
            return {"online": False, "error": f"HTTP {r.status_code}", "latency_ms": lat}
        except Exception as e:
            return {"online": False, "error": str(e), "latency_ms": round((time.time() - t0) * 1000, 1)}

class CloudOpenAICompatibleProvider(BaseAIProvider):
    """Optional Cloud AI Provider (OpenAI, Anthropic via bridge, or custom endpoint)."""
    name = "cloud-openai"
    is_local = False

    def __init__(
        self,
        api_base: str = "https://api.openai.com/v1",
        api_key: str = "",
        model: str = "gpt-4o-mini",
        timeout: float = 30.0
    ) -> None:
        self.api_base = api_base.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.timeout = timeout

    @property
    def masked_key(self) -> str:
        if not self.api_key:
            return "None"
        if len(self.api_key) <= 8:
            return "****"
        return f"{self.api_key[:4]}...{self.api_key[-4:]}"

    def generate(self, prompt: str, system: str = "", temperature: float = 0.3, max_tokens: int = 1024) -> str:
        if not self.api_key:
            raise ValueError("Cloud provider selected but no API key is configured.")
        url = f"{self.api_base}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        try:
            r = httpx.post(url, json=payload, headers=headers, timeout=self.timeout)
            if r.status_code == 200:
                data = r.json()
                choices = data.get("choices", [])
                if choices:
                    return choices[0].get("message", {}).get("content", "").strip()
                return ""
            raise RuntimeError(f"Cloud provider returned HTTP {r.status_code}: {r.text[:200]}")
        except Exception as e:
            raise RuntimeError(f"Cloud generation error: {e}") from e

    def test_connection(self) -> dict[str, Any]:
        if not self.api_key:
            return {"online": False, "error": "No API key configured.", "latency_ms": 0}
        t0 = time.time()
        try:
            url = f"{self.api_base}/models"
            headers = {"Authorization": f"Bearer {self.api_key}"}
            r = httpx.get(url, headers=headers, timeout=5.0)
            lat = round((time.time() - t0) * 1000, 1)
            if r.status_code == 200:
                return {
                    "online": True,
                    "latency_ms": lat,
                    "provider": self.name,
                    "model": self.model,
                    "masked_key": self.masked_key
                }
            return {"online": False, "error": f"HTTP {r.status_code}", "latency_ms": lat}
        except Exception as e:
            return {"online": False, "error": str(e), "latency_ms": round((time.time() - t0) * 1000, 1)}

class AIProviderManager:
    """Manages AI provider routing (local, cloud, hybrid)."""

    def __init__(self, mode: str = "local") -> None:
        self.mode = mode  # "local", "cloud", "hybrid"
        self.local_provider = LocalOllamaProvider()
        self.cloud_provider: Optional[CloudOpenAICompatibleProvider] = None
        self._load_config()

    def _load_config(self) -> None:
        cfg_path = Path("/run/media/prakash/TR_39/VOID/config/ai_providers.json")
        if cfg_path.exists():
            try:
                data = json.loads(cfg_path.read_text(encoding="utf-8"))
                self.mode = data.get("mode", "local")
                cloud_cfg = data.get("cloud", {})
                if cloud_cfg.get("enabled", False) and cloud_cfg.get("api_key"):
                    self.cloud_provider = CloudOpenAICompatibleProvider(
                        api_base=cloud_cfg.get("api_base", "https://api.openai.com/v1"),
                        api_key=cloud_cfg.get("api_key", ""),
                        model=cloud_cfg.get("model", "gpt-4o-mini")
                    )
            except Exception:
                pass

    def save_cloud_config(self, api_base: str, api_key: str, model: str, enabled: bool = True) -> None:
        """Saves cloud configuration safely to config."""
        cfg_path = Path("/run/media/prakash/TR_39/VOID/config/ai_providers.json")
        cfg_path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "mode": self.mode,
            "cloud": {
                "enabled": enabled,
                "api_base": api_base,
                "api_key": api_key,
                "model": model
            }
        }
        cfg_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        if enabled and api_key:
            self.cloud_provider = CloudOpenAICompatibleProvider(api_base, api_key, model)
        else:
            self.cloud_provider = None

    def route_provider(self, task_type: str = "general", is_sensitive: bool = False) -> BaseAIProvider:
        """
        Routes execution to local or cloud provider based on doctrine:
        - Sensitive data -> always local.
        - local mode -> always local.
        - cloud mode -> cloud if configured, fallback to local.
        - hybrid mode -> cloud for heavy tasks, local for general/offline.
        """
        if is_sensitive or self.mode == "local" or not self.cloud_provider:
            return self.local_provider

        if self.mode == "cloud":
            return self.cloud_provider

        if self.mode == "hybrid":
            if task_type in ["complex_planning", "heavy_code_analysis", "deep_research"]:
                return self.cloud_provider
            return self.local_provider

        return self.local_provider
