from __future__ import annotations

from typing import Optional

from dev_agent.core.context import ContextPacket
from dev_agent.core.session import SessionManager
from dev_agent.rag.retriever import RAGRetriever

from dev_agent.core.context.context_scorer import ContextScorer
from dev_agent.core.context.context_types import ContextItem


class ContextBuilder:
    """
    Centraliza construção de contexto do DevAgent.
    """

    def __init__(
        self,
        session: SessionManager,
        rag: RAGRetriever,
        memory=None,
        project_index=None,
    ) -> None:

        self.session = session
        self.rag = rag
        self.memory = memory
        self.project_index = project_index
        self.scorer = ContextScorer()


    def _compact(self, data) -> str:
        """
        Evita explodir tokens.
        """

        if isinstance(data, list):
            data = data[-5:]

        return str(data)[:1500]


    def _compact_history(self, history) -> str:
        if not history:
            return ""

        return "\n".join(
            f"{m['role']}: {m['content']}"
            for m in history[-8:]
        )

    def to_prompt(self, blocks):
        parts = []

        for block in blocks:

            if block.name == "memory":
                parts.append("=== MEMORY (HIGH PRIORITY) ===")
                parts.append(self._compact(block.data))

            elif block.name == "rag":
                parts.append("\n=== KNOWLEDGE BASE ===")
                parts.append(self._compact(block.data))

            elif block.name == "project":
                parts.append("\n=== PROJECT CONTEXT ===")
                parts.append(self._compact(block.data))

            elif block.name == "history":
                parts.append("\n=== HISTORY ===")
                parts.append(self._compact_history(block.data))

        return "\n".join(parts)

    # --------------------------------------------------------
    # BUILD PRINCIPAL
    # --------------------------------------------------------
    
    def build(self, user_input: str):

        items = []

        # ---------------- MEMORY ----------------
        for m in (self._get_memory(user_input) or []):
            items.append(ContextItem(
                source="memory",
                content=m,
                score=self.scorer.score_memory(user_input, m)
            ))

        # ---------------- RAG ----------------
        rag = self._get_rag(user_input)
        if rag:
            for chunk in rag.get("chunks", []):
                items.append(ContextItem(
                    source="rag",
                    content=chunk,
                    score=self.scorer.score_rag(user_input, chunk)
                ))

        # ---------------- PROJECT ----------------
        project = self._get_project(user_input)
        if project:
            items.append(ContextItem(
                source="project",
                content=project,
                score=self.scorer.score_project(user_input, str(project))
            ))

        # ---------------- SESSION ----------------
        for msg in self.session.get_messages()[-10:]:
            items.append(ContextItem(
                source="session",
                content=msg["content"],
                score=self.scorer.score_session(user_input, msg["content"])
            ))

        return self._rank(items)

    # --------------------------------------------------------
    # RAG
    # --------------------------------------------------------

    def _get_rag(self, query: str):
        if not self.rag.enabled:
            return None

        if not self.rag.should_use_rag(query):
            return None

        return self.rag.retrieve(query)

    # --------------------------------------------------------
    # MEMORY (stub v1)
    # --------------------------------------------------------

    def _get_memory(self, query: str):
        if not self.memory:
            return None

        return self.memory.search_text(query)

    # --------------------------------------------------------
    # PROJECT (stub v1)
    # --------------------------------------------------------

    def _get_project(self, query: str):
        if not self.project_index:
            return None

        # versão inicial: só resumo
        return {
            "files": len(self.project_index.index),
        }

    def _rank(self, items):
        items = sorted(items, key=lambda x: x.score, reverse=True)

        # limite de contexto (IMPORTANTE)
        return items[:15]