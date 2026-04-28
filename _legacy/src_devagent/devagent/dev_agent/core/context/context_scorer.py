import math
from typing import List
from dev_agent.core.context.context_types import ContextItem


class ContextScorer:
    """
    Calcula relevância de cada pedaço de contexto.
    """

    def score_memory(self, query: str, item: dict) -> float:
        text = item.get("content", "")
        return self._basic_relevance(query, text) * 1.2

    def score_rag(self, query: str, chunk: str) -> float:
        return self._basic_relevance(query, chunk) * 1.5

    def score_project(self, query: str, file_path: str) -> float:
        return self._basic_relevance(query, file_path)

    def score_session(self, query: str, message: str) -> float:
        return self._basic_relevance(query, message) * 0.8

    # -------------------------

    def _basic_relevance(self, query: str, text: str) -> float:
        if not text:
            return 0.0

        q_tokens = set(query.lower().split())
        t_tokens = set(str(text).lower().split())

        overlap = len(q_tokens & t_tokens)
        return overlap / (len(q_tokens) + 1e-5)