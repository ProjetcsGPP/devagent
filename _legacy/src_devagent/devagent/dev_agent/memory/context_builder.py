from __future__ import annotations

from typing import Dict, Any, List


class ContextBuilder:
    def __init__(self, project_index):
        self.project_index = project_index
        self.rag = None  # será injetado pelo router/sistema

    def build(self, query: str = "") -> Dict[str, Any]:

        base = {
            "summary": self._build_summary(self.project_index.index),
            "relevant_files": self._find_relevant_files(query),
            "dependency_hint": self._build_dependency_hint(self.project_index.index),
        }

        rag_context = self._rag_context(query)

        base["semantic"] = rag_context

        return base

    def _build_summary(self, index: Dict[str, Dict]) -> Dict[str, Any]:
        return {
            "total_files": len(index),
            "structure": list(index.keys())[:20]
        }

    def _find_relevant_files(self, query: str) -> List[str]:
        if not query:
            return []

        query_lower = query.lower()
        results = []

        for path in self.project_index.index.keys():
            if any(token in path.lower() for token in query_lower.split()):
                results.append(path)

        return results[:10]

    def _build_dependency_hint(self, index: Dict[str, Dict]) -> Dict[str, List[str]]:
        graph = {}

        for path, data in index.items():
            graph[path] = data.get("imports", [])

        return graph

    def _rag_context(self, query: str):
        """
        Injeta contexto semântico do RAG existente.
        """

        if not self.rag:
            return {
                "enabled": False,
                "content": None,
                "chunks": []
            }

        result = self.rag.retrieve_context(query)

        return result or {
            "enabled": False,
            "content": None,
            "chunks": []
        }