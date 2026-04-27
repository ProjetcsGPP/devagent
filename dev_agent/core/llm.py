"""
dev_agent/core/llm.py

Cliente Ollama para geração de texto e embeddings.
"""

from __future__ import annotations

import json
import requests
from typing import Dict, List, Optional

from dev_agent.config import (
    OLLAMA_HOST,
    MODEL_NAME,
    EMBEDDING_MODEL,
)


class OllamaError(Exception):
    """Exceção específica para erros do Ollama."""


class OllamaClient:
    """
    Cliente simples e robusto para comunicação com o Ollama.
    """

    def __init__(
        self,
        host: str = OLLAMA_HOST,
        model: str = MODEL_NAME,
        embedding_model: str = EMBEDDING_MODEL,
        timeout: int = 300,
    ) -> None:
        self.host = host.rstrip("/")
        self.model = model
        self.embedding_model = embedding_model
        self.timeout = timeout

    # ------------------------------------------------------------------
    # Métodos internos
    # ------------------------------------------------------------------

    def _post(self, endpoint: str, payload: Dict) -> Dict:
        """
        Executa requisição POST ao Ollama com tratamento robusto
        de timeout e erros de comunicação.
        """
        url = f"{self.host}{endpoint}"

        try:
            response = requests.post(
                url,
                json=payload,
                timeout=self.timeout,
            )

            response.raise_for_status()
            return response.json()

        except requests.exceptions.Timeout as exc:
            raise OllamaError(
                f"Tempo limite excedido ({self.timeout}s) "
                f"ao consultar o modelo."
            ) from exc

        except requests.exceptions.ConnectionError as exc:
            raise OllamaError(
                "Não foi possível conectar ao Ollama."
            ) from exc

        except requests.exceptions.HTTPError as exc:
            raise OllamaError(
                f"Erro HTTP do Ollama: {exc}"
            ) from exc

        except requests.exceptions.RequestException as exc:
            raise OllamaError(
                f"Erro ao comunicar com Ollama: {exc}"
            ) from exc

        except (ValueError, json.JSONDecodeError) as exc:
            raise OllamaError(
                "Resposta inválida recebida do Ollama."
            ) from exc

    # ------------------------------------------------------------------
    # Geração de texto
    # ------------------------------------------------------------------

    def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.2,
    ) -> str:
        """
        Gera resposta a partir de um prompt.
        """
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
            },
        }

        if system:
            payload["system"] = system

        result = self._post("/api/generate", payload)
        return result.get("response", "").strip()

    # ------------------------------------------------------------------
    # Chat
    # ------------------------------------------------------------------

    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.2,
    ) -> str:
        """
        Conversa utilizando histórico estruturado.
        """
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature,
            },
        }

        result = self._post("/api/chat", payload)
        return result["message"]["content"].strip()

    # ------------------------------------------------------------------
    # Embeddings
    # ------------------------------------------------------------------

    def embeddings(self, text: str) -> List[float]:
        """
        Gera embeddings para um texto.
        """
        payload = {
            "model": self.embedding_model,
            "prompt": text,
        }

        result = self._post("/api/embeddings", payload)
        return result["embedding"]

    # ------------------------------------------------------------------
    # Saúde do serviço
    # ------------------------------------------------------------------

    def is_available(self) -> bool:
        """
        Verifica se o Ollama está acessível.
        """
        try:
            response = requests.get(
                f"{self.host}/api/tags",
                timeout=10,
            )
            return response.status_code == 200
        except Exception:
            return False

    # ------------------------------------------------------------------
    # Informações
    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        return (
            f"OllamaClient("
            f"model='{self.model}', "
            f"host='{self.host}')"
        )