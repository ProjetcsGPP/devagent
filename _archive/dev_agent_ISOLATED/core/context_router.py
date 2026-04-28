from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List
from dataclasses import dataclass
from typing import Any, Dict, Optional
import math

@dataclass
class ContextBlock:
    name: str
    content: Any
    score: float
    tokens_estimate: int = 0

@dataclass
class ContextBlock:
    name: str
    data: Any
    score: float = 0.0
    """
    Responsável por priorizar e montar contexto inteligente.
    """

    def __init__(self, max_tokens: int = 3000):
        self.max_tokens = max_tokens

        from dev_agent.core.llm import OllamaClient

        self.llm = OllamaClient()

    # --------------------------------------------------------
    # MAIN ENTRY
    # --------------------------------------------------------

    def build(self, packet):
        blocks = []

        # MEMORY
        if packet.memory:
            blocks.append(ContextBlock(
                name="memory",
                data=packet.memory,
                score=self._score_memory(packet)
            ))

        # PROJECT
        if packet.project:
            blocks.append(ContextBlock(
                name="project",
                data=packet.project,
                score=self._score_project(packet)
            ))

        # RAG
        if packet.rag:
            blocks.append(ContextBlock(
                name="rag",
                data=packet.rag,
                score=self._score_rag(packet)
            ))

        # HISTORY (sempre último)
        if packet.history:
            blocks.append(ContextBlock(
                name="history",
                data=packet.history,
                score=self._score_history(packet)
            ))

        # ORDENAR POR RELEVÂNCIA
        blocks.sort(key=lambda x: x.score, reverse=True)

        return blocks


    def _embed(self, text: str):
        try:
            return self.llm.embeddings(text)
        except:
            return []


    # --------------------------------------------------------
    # SCORING
    # --------------------------------------------------------

    def _score_memory(self, packet) -> float:
        if not packet.memory:
            return 0.0

        score = 0.7  # base alta

        # boost se contém match direto
        if hasattr(packet.memory, "__len__") and len(str(packet.memory)) > 0:
            score += 0.2

        return min(score, 1.0)


    def _score_project(self, packet) -> float:
        if not packet.project:
            return 0.0

        return 0.6


    def _score_rag(self, packet) -> float:
        if not packet.rag:
            return 0.0

        return 0.8


    def _score_history(self, packet) -> float:
        if not packet.history:
            return 0.0

        return 0.3

    def _cosine(self, a, b):
        if not a or not b:
            return 0.0

        dot = sum(x*y for x, y in zip(a, b))
        na = math.sqrt(sum(x*x for x in a))
        nb = math.sqrt(sum(x*x for x in b))

        if na == 0 or nb == 0:
            return 0.0

        return dot / (na * nb)

    def _tag_boost(self, query: str, tags: list):
        q = query.lower()

        for t in tags:
            if t.lower() in q:
                return 1.0

        return 0.0

    def _score_blocks(self, ctx, query: str):

        blocks = []

        query_vec = self._embed(query)

        # -------------------------
        # MEMORY (semântico)
        # -------------------------
        if ctx.memory:
            blocks.append(
                ContextBlock(
                    name="memory",
                    content=ctx.memory,
                    score=self._score_memory(ctx.memory, query_vec, query),
                    tokens_estimate=self._estimate(ctx.memory),
                )
            )

        # -------------------------
        # PROJECT (semântico)
        # -------------------------
        if ctx.project:
            blocks.append(
                ContextBlock(
                    name="project",
                    content=ctx.project,
                    score=self._score_project(ctx.project, query_vec, query),
                    tokens_estimate=self._estimate(ctx.project),
                )
            )

        # -------------------------
        # RAG (semântico)
        # -------------------------
        if ctx.rag:
            blocks.append(
                ContextBlock(
                    name="rag",
                    content=ctx.rag,
                    score=self._score_rag(ctx.rag, query_vec),
                    tokens_estimate=self._estimate(ctx.rag),
                )
            )

        # -------------------------
        # HISTORY (fraco, só contexto)
        # -------------------------
        if ctx.history:
            last = ctx.history[-6:]

            blocks.append(
                ContextBlock(
                    name="history",
                    content=last,
                    score=0.2,
                    tokens_estimate=len(last) * 20,
                )
            )

        return blocks

    # --------------------------------------------------------
    # SELECTION (budget-aware greedy)
    # --------------------------------------------------------

    def _select_blocks(self, blocks: List[ContextBlock]) -> List[ContextBlock]:

        blocks.sort(key=lambda b: b.score, reverse=True)

        selected = []
        used_tokens = 0

        for b in blocks:
            if used_tokens + b.tokens_estimate > self.max_tokens:
                continue

            selected.append(b)
            used_tokens += b.tokens_estimate

        return selected

    # --------------------------------------------------------
    # RENDER
    # --------------------------------------------------------

    def _render(self, blocks: List[ContextBlock]) -> str:

        parts = []

        for b in blocks:

            parts.append(f"\n=== {b.name.upper()} ===")

            if isinstance(b.content, list):
                for item in b.content:
                    parts.append(str(item))
            else:
                parts.append(str(b.content))

        return "\n".join(parts)

    # --------------------------------------------------------
    # SIMPLE TOKEN ESTIMATE
    # --------------------------------------------------------

    def _estimate(self, obj: Any) -> int:
        return len(str(obj)) // 4