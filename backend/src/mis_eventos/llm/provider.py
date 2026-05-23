"""Provider-agnostic de LLM - reutiliza el patron de LexAudit.

El acceso al LLM esta aislado en una sola funcion. Si maniana cambiamos de
Groq a otro proveedor, solo tocamos este archivo. El resto del sistema no
necesita saber que proveedor estamos usando.

Esto es un bonus opcional - el sistema funciona sin LLM. Si la GROQ_API_KEY
no esta configurada, el endpoint de IA devuelve HTTP 503 con mensaje claro.
"""

import os
from typing import Protocol

import httpx


class LlmProvider(Protocol):
    def generate(self, system: str, user: str, max_tokens: int = 500) -> str:
        ...


class GroqProvider:
    """Llamadas al API de Groq (compatible OpenAI)."""

    BASE_URL = "https://api.groq.com/openai/v1/chat/completions"
    DEFAULT_MODEL = "llama-3.3-70b-versatile"

    def __init__(self, api_key: str, model: str | None = None) -> None:
        self.api_key = api_key
        self.model = model or self.DEFAULT_MODEL

    def generate(self, system: str, user: str, max_tokens: int = 500) -> str:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "max_tokens": max_tokens,
            "temperature": 0.7,
        }
        response = httpx.post(self.BASE_URL, json=payload, headers=headers, timeout=30.0)
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"].strip()


def get_llm() -> LlmProvider:
    """Devuelve el LLM provider configurado.

    Lee GROQ_API_KEY del entorno. Si no esta seteada, lanza ValueError.
    El caller debe manejar el error y devolver HTTP 503.
    """
    api_key = os.getenv("GROQ_API_KEY", "").strip()
    if not api_key:
        raise ValueError(
            "GROQ_API_KEY no esta configurada - el bonus de IA esta deshabilitado"
        )
    return GroqProvider(api_key)
