from collections import defaultdict
from typing import List, Dict, Any
import time


class MIL:
    """
    Memory Intelligence Layer FINAL

    Responsabilidade:
    - rankear contexto
    - aprender com execução
    - evitar loops
    - evoluir tags e relevância
    """

    def __init__(self, storage, file_tags_repo):
        self.storage = storage
        self.file_tags = file_tags_repo

        self.tag_score = defaultdict(float)
        self.error_frequency = defaultdict(int)
        self.strategy_score = defaultdict(float)

    # =========================================================
    # PUBLIC API
    # =========================================================

    def build_context(self, query: str, brain=None):

        rag = self._rag(query)
        tag_scores = self._tags(query)
        exec_scores = self._execution(query)
        loop_penalty = self._loop_detection(query)
        strategy_boost = self._brain(brain)

        return self._merge(
            rag,
            tag_scores,
            exec_scores,
            loop_penalty,
            strategy_boost
        )

    # =========================================================
    # RAG
    # =========================================================

    def _rag(self, query: str):
        return self.storage.fetchall("""
            SELECT path, content
            FROM files_index
            WHERE content LIKE ?
            LIMIT 20
        """, (f"%{query}%",))

    # =========================================================
    # TAG SYSTEM (peso semântico)
    # =========================================================

    def _tags(self, query: str):

        rows = self.storage.fetchall("""
            SELECT file_path, tag, weight, confidence
            FROM file_tags
        """)

        scores = defaultdict(float)

        for path, tag, weight, confidence in rows:

            if tag.lower() in query.lower():
                scores[path] += weight * confidence

        return scores

    # =========================================================
    # EXECUTION MEMORY (aprendizado real)
    # =========================================================

    def _execution(self, query: str):

        rows = self.storage.fetchall("""
            SELECT intent, success, error_type
            FROM execution_memory
            ORDER BY id DESC
            LIMIT 300
        """)

        scores = defaultdict(float)

        for intent, success, error in rows:

            if query.lower() in str(intent).lower():

                score = 1.5 if success else -2.0

                scores[str(intent)] += score

                if error:
                    self.error_frequency[(intent, error)] += 1

        return scores

    # =========================================================
    # LOOP DETECTION (ANTI-REPETIÇÃO REAL)
    # =========================================================

    def _loop_detection(self, query: str):

        penalty = defaultdict(float)

        for (intent, error), count in self.error_frequency.items():

            if query.lower() in str(intent).lower():

                if count >= 3:
                    penalty[intent] -= 3.0

        return penalty

    # =========================================================
    # BRAIN INFLUENCE
    # =========================================================

    def _brain(self, brain):

        if not brain:
            return {}

        return dict(brain.strategy_score)

    # =========================================================
    # CORE MERGE (INTELIGÊNCIA FINAL)
    # =========================================================

    def _merge(self, rag, tags, exec_scores, loop_penalty, brain_scores):

        ranking = {}

        # RAG base
        for path, content in rag:
            ranking[path] = {"content": content, "score": 1.0}

        # TAGS
        for path, score in tags.items():
            if path not in ranking:
                ranking[path] = {"content": "", "score": 0.5}

            ranking[path]["score"] += score

        # EXECUTION
        for key, score in exec_scores.items():

            path = self._resolve(key)

            if not path:
                continue

            if path not in ranking:
                ranking[path] = {"content": "", "score": 0.3}

            ranking[path]["score"] += score

        # LOOP PENALTY
        for key, penalty in loop_penalty.items():

            path = self._resolve(key)

            if path in ranking:
                ranking[path]["score"] += penalty

        # BRAIN GLOBAL INFLUENCE
        for value in brain_scores.values():
            for item in ranking.values():
                item["score"] += value * 0.02

        return sorted(ranking.items(), key=lambda x: x[1]["score"], reverse=True)

    # =========================================================
    # LEARNING LOOP (ESSÊNCIA DO SISTEMA)
    # =========================================================

    def learn(self, intent, success: bool, files_used: List[str]):

        for file_path in files_used:

            tags = self.file_tags.get_by_file(file_path)

            for tag in tags:

                delta = 0.2 if success else -0.3

                self.storage.execute("""
                    UPDATE file_tags
                    SET weight = weight + ?
                    WHERE file_path = ? AND tag = ?
                """, (delta, file_path, tag.tag))

    # =========================================================
    # HELPERS
    # =========================================================

    def _resolve(self, key: str):
        row = self.storage.fetchall("""
            SELECT file_path FROM file_tags WHERE tag = ? LIMIT 1
        """, (key,))

        return row[0][0] if row else None