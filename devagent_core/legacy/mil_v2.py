import math
from collections import defaultdict


class MILv2:
    """
    Memory Intelligence Layer v2
    - RAG + Tags + Ranking
    """

    def __init__(self, storage):
        self.storage = storage

    # =========================================================
    # MAIN ENTRY
    # =========================================================
    def retrieve_context(self, query: str, limit: int = 5) -> str:

        # 1. busca textual (RAG base)
        rag_results = self._rag_search(query, limit=limit)

        # 2. busca por tags (semântica estruturada)
        tag_results = self._tag_search(query)

        # 3. merge + ranking
        merged = self._merge_and_rank(rag_results, tag_results)

        # 4. montagem final do contexto
        return self._build_context(merged)

    # =========================================================
    # RAG SEARCH (base atual do index_service)
    # =========================================================
    def _rag_search(self, query: str, limit: int):
        return self.storage.fetchall(
            """
            SELECT path, content
            FROM files_index
            WHERE content LIKE ?
            LIMIT ?
            """,
            (f"%{query}%", limit),
        )

    # =========================================================
    # TAG SEARCH (novo cérebro)
    # =========================================================
    def _tag_search(self, query: str):

        words = set(query.lower().split())

        rows = self.storage.fetchall(
            """
            SELECT path, tag, weight
            FROM file_tags
            """
        )

        scores = defaultdict(float)

        for path, tag, weight in rows:

            tag_tokens = set(tag.lower().split())

            overlap = len(words & tag_tokens)

            if overlap > 0:
                scores[path] += overlap * float(weight)

        return scores

    # =========================================================
    # MERGE + RANKING INTELIGENTE
    # =========================================================

    def _get_success_boost_from_path(self, path: str) -> float:
        """
        Calcula o quanto esse arquivo contribui para sucesso histórico.
        """

        rows = self.storage.fetchall("""
            SELECT AVG(
                CASE WHEN el.success = 1 THEN 1.0 ELSE 0.0 END
            )
            FROM execution_log el
            JOIN file_tags ft ON ft.tag = el.intent
            WHERE ft.file_path = ?
        """, (path,))

        if not rows or rows[0][0] is None:
            return 1.0

        # suavização (evita extremos)
        return 0.5 + float(rows[0][0])
    
    def _merge_and_rank(self, rag_results, tag_scores):

        ranking = {}

        # --- score base RAG ---
        for path, content in rag_results:
            ranking[path] = {
                "content": content,
                "score": 1.0
            }

        # --- boost por tags (AGORA COM LEARNING) ---
        for path, score in tag_scores.items():

            if path not in ranking:
                row = self.storage.fetchone(
                    """
                    SELECT content FROM files_index WHERE path = ?
                    """,
                    (path,),
                )

                if not row:
                    continue

                ranking[path] = {
                    "content": row[0],
                    "score": 0.5
                }

            # 🔥 NOVO: fator de aprendizado baseado em execução histórica
            success_boost = self._get_success_boost_from_path(path)

            # 🔥 score inteligente (ANTES era só += score)
            ranking[path]["score"] += score * success_boost
            
        # ordena por relevância
        sorted_items = sorted(
            ranking.items(),
            key=lambda x: x[1]["score"],
            reverse=True
        )

        return sorted_items

    # =========================================================
    # CONTEXT BUILDER
    # =========================================================
    def _build_context(self, ranked_items):

        chunks = []

        for path, data in ranked_items[:5]:

            chunks.append(
                f"""
### FILE: {path}
SCORE: {data['score']}

{data['content'][:2000]}
"""
            )

        return "\n".join(chunks)
        