from __future__ import annotations

import requests


class OllamaError(RuntimeError):
    """Raised when the local Ollama service cannot complete a request."""


class OllamaClient:
    def __init__(self, host: str, model: str, timeout_seconds: int = 180) -> None:
        self.host = host.rstrip("/")
        self.model = model
        self.timeout_seconds = timeout_seconds

    def chat_json(self, *, system_prompt: str, user_prompt: str, schema: dict) -> str:
        payload = {
            "model": self.model,
            "stream": False,
            "think": False,
            "format": schema,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "options": {"temperature": 0.2, "num_predict": 1400},
        }
        try:
            response = requests.post(
                f"{self.host}/api/chat",
                json=payload,
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
        except requests.ConnectionError as exc:
            raise OllamaError(
                f"Could not connect to Ollama at {self.host}. Open Ollama and try again."
            ) from exc
        except requests.Timeout as exc:
            raise OllamaError(
                f"Ollama did not respond within {self.timeout_seconds} seconds."
            ) from exc
        except requests.HTTPError as exc:
            detail = response.text[:500]
            raise OllamaError(f"Ollama returned an error: {detail}") from exc

        try:
            data = response.json()
            return data["message"]["content"]
        except (ValueError, KeyError, TypeError) as exc:
            raise OllamaError("Ollama returned an unexpected response format.") from exc
