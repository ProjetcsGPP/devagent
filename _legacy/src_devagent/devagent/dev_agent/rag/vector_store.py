"""
Armazena embeddings e permite busca semântica.
"""

from typing import List, Dict


class VectorStore:
    def __init__(self):
        self.vectors = []  # (embedding, metadata)

    # --------------------------------------------------------
    # STORE
    # --------------------------------------------------------

    def add(self, embedding: List[float], metadata: Dict):
        self.vectors.append((embedding, metadata))

    # --------------------------------------------------------
    # SEARCH (SIMPLIFICADO AQUI - FUTURO: FAISS / CHROMA)
    # --------------------------------------------------------

    def search(self, query_embedding: List[float], top_k: int = 5):
        """
        Busca vetorial (placeholder simples).
        """

        return [meta for _, meta in self.vectors[:top_k]]