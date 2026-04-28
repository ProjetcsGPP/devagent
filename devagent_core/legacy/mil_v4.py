import time
from collections import defaultdict
from typing import List, Dict, Any


class MILv4:
    """
    Memory Intelligence Layer v4
    - aprendizado contínuo
    - ranking semântico + comportamental
    - feedback do Brain + Execução + Tags
    """

    def __init__(self, storage, file_tags_repo):
        self.storage = storage
        self.file_tags = file_tags_repo

        # memória viva (cache)
        self.tag_strength = defaultdict(float)
        self.success_memory = defaultdict(float)
        self.strategy_memory = defaultdict(float)

    # =========================================================
    # PUBLIC API
    # =========================================================

    def build_context(self, query: str, brain=None) -> List[tuple]:
        """
        Entrada principal do MIL:
        retorna arquivos ranqueados com inteligência híbrida.
        """

        rag_results = self._rag_search(query)
        tag_scores = self._score_by_tags(query)
        exec_scores = self._score_by_execution(query)
        strategy_boost = self._score_by_strategy(brain)

        ranked = self._merge_and_rank(
            rag_results,
            tag_scores,
            exec_scores,
            strategy_boost
        )

        return ranked

    # =========================================================
    # RAG BASE
    # =========================================================

    def _rag_search(self, query: str):
        rows = self.storage.fetchall("""
            SELECT path, content
            FROM files_index
            WHERE content LIKE ?
            LIMIT 20
        """, (f"%{query}%",))

        return rows

    # =========================================================
    # TAG SCORING
    # =========================================================

    def _score_by_tags(self, query: str) -> Dict[str, float]:

        tag_rows = self.storage.fetchall("""
            SELECT file_path, tag, weight, confidence
            FROM file_tags
        """)

        scores = defaultdict(float)

        for path, tag, weight, confidence in tag_rows:

            overlap = self._text_overlap(query, tag)

            if overlap == 0:
                continue

            score = overlap * weight * confidence

            scores[path] += score

        return scores

    # =========================================================
    # EXECUTION HISTORY SCORING
    # =========================================================

    def _score_by_execution(self, query: str) -> Dict[str, float]:

        rows = self.storage.fetchall("""
            SELECT intent, plan, success
            FROM execution_memory
            ORDER BY id DESC
            LIMIT 200
        """)

        scores = defaultdict(float)

        for intent, plan, success in rows:

            overlap = self._text_overlap(query, str(intent))

            if overlap == 0:
                continue

            success_boost = 1.8 if success else -1.2

            score = overlap * success_boost

            scores[str(intent)] += score

        return scores

    # =========================================================
    # STRATEGY INFLUENCE (Brain)
    # =========================================================

    def _score_by_strategy(self, brain) -> Dict[str, float]:

        if not brain:
            return {}

        scores = {}

        for strategy, value in brain.strategy_score.items():
            scores[strategy] = value

        return scores

    # =========================================================
    # MERGE + RANK (CORE INTELLIGENCE)
    # =========================================================

    def _merge_and_rank(
        self,
        rag_results,
        tag_scores,
        exec_scores,
        strategy_scores
    ):

        ranking = {}

        # -------------------------
        # RAG base score
        # -------------------------
        for path, content in rag_results:

            ranking[path] = {
                "content": content,
                "score": 1.0
            }

        # -------------------------
        # TAG boost
        # -------------------------
        for path, score in tag_scores.items():

            if path not in ranking:
                content = self._load_content(path)
                ranking[path] = {
                    "content": content,
                    "score": 0.5
                }

            ranking[path]["score"] += score

        # -------------------------
        # EXECUTION memory boost
        # -------------------------
        for key, score in exec_scores.items():

            path = self._resolve_to_path(key)

            if not path:
                continue

            if path not in ranking:
                content = self._load_content(path)
                ranking[path] = {
                    "content": content,
                    "score": 0.3
                }

            ranking[path]["score"] += score

        # -------------------------
        # STRATEGY global influence
        # -------------------------
        strategy_boost = sum(strategy_scores.values()) * 0.05

        for item in ranking.values():
            item["score"] += strategy_boost

        # -------------------------
        # FINAL SORT
        # -------------------------
        sorted_items = sorted(
            ranking.items(),
            key=lambda x: x[1]["score"],
            reverse=True
        )

        return sorted_items

    # =========================================================
    # LEARNING LOOP (AUTO-EVOLUÇÃO)
    # =========================================================

    def learn_from_execution(self, intent, plan, success, files_used: List[str]):

        for file_path in files_used:

            tags = self.file_tags.get_by_file(file_path)

            for tag in tags:

                key = tag.tag

                if success:
                    self.tag_strength[key] += 0.2
                else:
                    self.tag_strength[key] -= 0.3

                # persistência evolutiva no SQLite
                self.storage.execute("""
                    UPDATE file_tags
                    SET weight = weight + ?
                    WHERE file_path = ? AND tag = ?
                """, (
                    0.1 if success else -0.2,
                    file_path,
                    tag.tag
                ))

    # =========================================================
    # HELPERS
    # =========================================================

    def _text_overlap(self, text: str, tag: str) -> float:
        text = text.lower()
        tag = tag.lower()

        if tag in text:
            return 1.0

        # overlap parcial simples
        common = set(text.split()) & set(tag.split())

        return len(common) / (len(tag.split()) + 1)

    def _load_content(self, path: str):
        row = self.storage.fetchone("""
            SELECT content FROM files_index WHERE path = ?
        """, (path,))

        return row[0] if row else ""

    def _resolve_to_path(self, key: str):
        # pode evoluir depois (mapping de intents → files)
        row = self.storage.fetchone("""
            SELECT file_path FROM file_tags WHERE tag = ? LIMIT 1
        """, (key,))

        return row[0] if row else None