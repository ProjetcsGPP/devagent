"""
dev_agent/rag/retriever.py

Integração com o RAG local existente.
"""

from __future__ import annotations

import sys
from typing import Optional, Any

from dev_agent.config import BASE_DIR, ENABLE_RAG


class RAGRetriever:
    """
    Wrapper para reutilizar o sistema RAG já existente.
    """

    def __init__(self) -> None:
        self.enabled = ENABLE_RAG
        self._query_function = None

        if self.enabled:
            self._load_query_module()

    # ------------------------------------------------------------------
    # Carregamento dinâmico
    # ------------------------------------------------------------------

    def _load_query_module(self) -> None:
        """
        Carrega dinamicamente o módulo query.py existente.
        """
        try:
            workspace = str(BASE_DIR)

            if workspace not in sys.path:
                sys.path.insert(0, workspace)

            from query import retrieve  # type: ignore

            self._query_function = retrieve

        except Exception as exc:
            print(f"[RAG] Aviso: RAG indisponível ({exc})")
            self.enabled = False

    # ------------------------------------------------------------------
    # API: RETRIEVE (RAW)
    # ------------------------------------------------------------------

    def retrieve(self, question: str) -> Any:
        """
        Recupera dados brutos do RAG.
        NÃO faz normalização aqui.
        """

        if not self.enabled or not self._query_function:
            return None

        try:
            return self._query_function(question)

        except Exception as exc:
            print(f"[RAG] Erro durante recuperação: {exc}")
            return None

    # ------------------------------------------------------------------
    # NORMALIZAÇÃO SEGURA
    # ------------------------------------------------------------------

    def normalize(self, result: Any) -> str:
        """
        Normaliza qualquer saída do RAG para string segura.
        """

        if result is None:
            return ""

        if isinstance(result, str):
            return result.strip()

        if isinstance(result, dict):
            text = (
                result.get("text")
                or result.get("content")
                or result.get("chunk")
                or result.get("document")
            )
            return self.normalize(text if text is not None else str(result))

        if isinstance(result, list):
            return "\n\n".join(
                self.normalize(item) for item in result if item is not None
            ).strip()

        return str(result).strip()

    # ------------------------------------------------------------------
    # CONTEXT (DEVAGENT v6)
    # ------------------------------------------------------------------

    def retrieve_context(self, question: str) -> dict:
        """
        Versão estruturada para o DevAgent v6.
        """

        raw = self.retrieve(question)
        text = self.normalize(raw)

        if not text:
            return {
                "enabled": False,
                "content": None,
                "chunks": []
            }

        chunks = text.split("\n\n")

        return {
            "enabled": True,
            "content": text,
            "chunks": chunks[:10],
        }

    # ------------------------------------------------------------------
    # HEURÍSTICA
    # ------------------------------------------------------------------

    def should_use_rag(self, question: str) -> bool:
        """
        Heurística inicial para decidir uso do RAG.
        """
        question = question.lower()

        keywords = {
            "api",
            "endpoint",
            "swagger",
            "login",
            "autenticar",
            "token",
            "rota",
            "documentação",
            "authentication",
            "authorization",
        }

        return any(keyword in question for keyword in keywords)

    # ------------------------------------------------------------------
    # REPRESENTAÇÃO
    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        status = "enabled" if self.enabled else "disabled"
        return f"RAGRetriever({status})"