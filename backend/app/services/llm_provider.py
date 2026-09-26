"""Shared LLM interface, also copied into isolated pipeline workdirs."""
import os
from abc import ABC, abstractmethod
from urllib.parse import urlparse

import httpx


class ProviderError(RuntimeError):
    pass


class LLMProvider(ABC):
    @abstractmethod
    def chat(self, messages, options=None, format=None):
        """Return the existing pipeline's message/content response shape."""

    def health(self):
        response = self.chat([{"role": "user", "content": "Reply with OK."}], {"num_predict": 32})
        if not response.get("message", {}).get("content", "").strip():
            raise ProviderError("AI returned an empty response.")

    def metadata(self):
        return {"mode": self.mode, "provider": self.provider, "model": self.model, "retrieval": os.getenv("BIDLENS_RETRIEVAL", "minilm")}


class OllamaProvider(LLMProvider):
    mode, provider, model = "OFFLINE", "Ollama", "qwen2.5:3b"

    def __init__(self):
        self.url = os.getenv("OLLAMA_LOCAL_URL", "http://127.0.0.1:11434").rstrip("/")

    def _validate_endpoint(self):
        if os.getenv("APP_ENV") == "production":
            raise ProviderError("Offline Ollama is available only in local development. Use Online / Groq on this hosted demo.")
        if urlparse(self.url).hostname not in {"localhost", "127.0.0.1", "::1"}:
            raise ProviderError("Offline mode requires Ollama on the backend machine's loopback address.")

    def chat(self, messages, options=None, format=None):
        self._validate_endpoint()
        try:
            payload = {"model": self.model, "messages": messages, "stream": False, "options": options or {"temperature": 0}}
            if format:
                payload["format"] = format
            response = httpx.post(f"{self.url}/api/chat", json=payload, timeout=300)
            response.raise_for_status()
            return response.json()
        except (httpx.HTTPError, ValueError) as error:
            raise ProviderError("Offline AI is currently unavailable. Start Ollama and ensure qwen2.5:3b is installed, or switch to Online Mode.") from error

    def health(self):
        self._validate_endpoint()
        try:
            response = httpx.get(f"{self.url}/api/tags", timeout=10)
            response.raise_for_status()
            if not any(model.get("name") == self.model for model in response.json().get("models", [])):
                raise ValueError("Model not installed")
        except (httpx.HTTPError, ValueError) as error:
            raise ProviderError("Offline AI is currently unavailable. Start Ollama and ensure qwen2.5:3b is installed, or switch to Online Mode.") from error
        super().health()


class GroqProvider(LLMProvider):
    mode, provider = "ONLINE", "Groq"

    def __init__(self):
        self.model = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")

    def chat(self, messages, options=None, format=None):
        key = os.getenv("GROQ_API_KEY", "").strip()
        if not key:
            raise ProviderError("Online AI is unavailable. Configure GROQ_API_KEY in the backend Environment settings. The preprocessed demo remains available.")
        try:
            payload = {"model": self.model, "messages": messages, "stream": False, "temperature": 0}
            payload["max_completion_tokens"] = max(1024, min((options or {}).get("num_predict", 3000), 3000))
            if self.model.startswith("openai/gpt-oss"):
                payload["reasoning_effort"] = "low"
            if format == "json":
                payload["response_format"] = {"type": "json_object"}
            response = httpx.post("https://api.groq.com/openai/v1/chat/completions", headers={"Authorization": f"Bearer {key}"}, json=payload, timeout=90)
            if response.status_code != 200:
                raise ProviderError(f"Groq request failed (HTTP {response.status_code}). Check API key, model access or free-tier rate limits. No fallback was used; the preprocessed demo remains available.")
            if response.json()["choices"][0].get("finish_reason") == "length":
                raise ProviderError("Groq output reached its token limit. No partial extraction was accepted. The preprocessed demo remains available.")
            content = response.json()["choices"][0]["message"]["content"]
            if not isinstance(content, str) or not content.strip():
                raise ValueError("Empty content")
            if content.strip().startswith("```"):
                content = "\n".join(content.strip().splitlines()[1:-1])
            return {"message": {"content": content}}
        except (httpx.HTTPError, ValueError, KeyError, IndexError) as error:
            raise ProviderError("Groq could not return a valid response. Check network access and backend configuration. The preprocessed demo remains available.") from error


def get_provider(mode):
    if mode == "OFFLINE":
        return OllamaProvider()
    if mode == "ONLINE":
        return GroqProvider()
    raise ProviderError("Choose a processing mode before running AI.")


def chat(*, messages, model=None, options=None, **kwargs):
    return get_provider(os.getenv("BIDLENS_AI_MODE", "OFFLINE")).chat(messages, options, kwargs.get("format"))
