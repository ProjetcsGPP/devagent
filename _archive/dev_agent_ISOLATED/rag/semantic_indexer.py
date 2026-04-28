"""
DevAgent v6 - Semantic Indexer

Converte código-fonte em chunks semânticos para embeddings.
"""

from __future__ import annotations

from typing import List, Dict


class SemanticIndexer:
    def __init__(self, project_index):
        self.project_index = project_index
        self.chunks: List[Dict] = []

    # --------------------------------------------------------
    # BUILD SEMANTIC CHUNKS
    # --------------------------------------------------------

    def build(self) -> List[Dict]:
        """
        Transforma arquivos em chunks semânticos.
        """

        self.chunks = []

        for path, data in self.project_index.get_index().items():

            try:
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()

                self.chunks.append({
                    "path": path,
                    "content": content,
                    "type": self._detect_type(content),
                })

            except Exception:
                continue

        return self.chunks

    # --------------------------------------------------------
    # DETECÇÃO SEMÂNTICA SIMPLES
    # --------------------------------------------------------

    def _detect_type(self, content: str) -> str:
        """
        Classifica o tipo de código.
        """

        if "class " in content:
            return "class"

        if "def " in content:
            return "function"

        return "module"