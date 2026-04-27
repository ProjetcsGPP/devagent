"""
Camada de embeddings.

Aqui você pode plugar:
- OpenAI embeddings
- sentence-transformers
- Ollama embeddings
"""

from typing import List


class Embeddings:
    def encode(self, text: str) -> List[float]:
        """
        Placeholder simples.
        Substituir depois por modelo real.
        """

        # versão mock (hash-based simplificado)
        return [float(ord(c) % 10) for c in text[:64]]