import time
from collections import defaultdict
from typing import List, Dict, Any


class MILv5:
    """
    MIL v5 = sistema cognitivo auto-evolutivo do DevAgent

    Agora o sistema:
    - cria tags automaticamente
    - detecta loops de erro
    - aprende padrões de falha
    - ajusta estratégias do Brain
    """

    def __init__(self, storage, file_tags_repo):
        self.storage = storage
        self.file_tags = file_tags_repo

        # memória dinâmica
        self.tag_strength = defaultdict(float)
        self.error_patterns = defaultdict(int)
        self.strategy_score = defaultdict(float)
        self.failure_graph = defaultdict(list)

    # =========================================================
    # ENTRY POINT
    # =========================================================

    def build_context(self, query: str, brain=None):

        rag = self._rag(query)
        tags = self._tag_score(query)
        exec_mem = self._execution_score(query)
        anti_loop = self._loop_penalty(query)

        ranked = self._merge(rag, tags, exec_mem, anti_loop, brain)

        return ranked

    # =========================================================
    # RAG BASE
    # =========================================================

    def _rag(self, query: str):

        rows = self.storage.fetchall("""
            SELECT path, content
            FROM files_index
            WHERE content LIKE ?
            LIMIT 20
        """, (f"%{query}%",))

        return rows

    # =========================================================
    # TAG SCORING + AUTO DISCOVERY
    # =========================================================

    def _tag_score(self, query: str):

        rows = self.storage.fetchall("""
            SELECT file_path, tag, weight, confidence
            FROM file_tags
        """)

        scores = defaultdict(float)

        for path, tag, weight, confidence in rows:

            overlap = self._overlap(query, tag)

            if overlap == 0:
                continue

            score = overlap * weight * confidence

            scores[path] += score

            # 🧠 AUTO TAG DISCOVERY
            if overlap > 0.7:
                self._auto_discover_tag(query, path)

        return scores

    # =========================================================
    # EXECUTION MEMORY
    # =========================================================

    def _execution_score(self, query: str):

        rows = self.storage.fetchall("""
            SELECT intent, plan, success
            FROM execution_memory
            ORDER BY id DESC
            LIMIT 300
        """)

        scores = defaultdict(float)

        for intent, plan, success in rows:

            overlap = self._overlap(query, str(intent))

            if overlap == 0:
                continue

            boost = 2.0 if success else -2.5

            scores[str(intent)] += overlap * boost

        return scores

    # =========================================================
    # LOOP DETECTION (NOVO NÚCLEO)
    # =========================================================

    def _loop_penalty(self, query: str):

        penalty = defaultdict(float)

        history = self.storage.fetchall("""
            SELECT intent, error_type
            FROM execution_memory
            ORDER BY id DESC
            LIMIT 200
        """)

        for intent, error in history:

            key = f"{intent}:{error}"

            self.error_patterns[key] += 1

            if self.error_patterns[key] > 2:

                # LOOP DETECTED
                penalty[intent] -= 3.0

                self.failure_graph[intent].append(error)

        return penalty

    # =========================================================
    # AUTO TAG GENERATION (NOVO)
    # =========================================================

    def _auto_discover_tag(self, query: str, file_path: str):

        words = query.lower().split()

        for w in words:

            if len(w) < 4:
                continue

            self.storage.execute("""
                INSERT OR IGNORE INTO file_tags
                (file_path, tag, tag_type, weight, confidence, source, created_at, updated_at)
                VALUES (?, ?, 'auto', 0.6, 0.5, 'mil_v5', ?, ?)
            """, (
                file_path,
                w,
                time.time(),
                time.time()
            ))

    # =========================================================
    # STRATEGY EVOLUTION (BRAIN COUPLING)
    # =========================================================

    def evolve_strategies(self, brain):

        for strategy, score in brain.strategy_score.items():

            self.strategy_score[strategy] += score * 0.1

            # penaliza estratégias que geram loops
            if strategy in self.failure_graph:
                self.strategy_score[strategy] -= len(self.failure_graph[strategy])

    # =========================================================
    # MERGE CORE (INTELIGÊNCIA FINAL)
    # =========================================================

    def _merge(self, rag, tags, exec_mem, loop_penalty, brain):

        ranking = {}

        # RAG base
        for path, content in rag:
            ranking[path] = {"content": content, "score": 1.0}

        # TAGS
        for path, score in tags.items():
            if path not in ranking:
                ranking[path] = {"content": self._load(path), "score": 0.5}

            ranking[path]["score"] += score

        # EXEC memory
        for key, score in exec_mem.items():

            path = self._resolve(key)

            if not path:
                continue

            if path not in ranking:
                ranking[path] = {"content": self._load(path), "score": 0.3}

            ranking[path]["score"] += score

        # LOOP penalty (ANTI REPETIÇÃO)
        for key, penalty in loop_penalty.items():

            path = self._resolve(key)

            if path in ranking:
                ranking[path]["score"] += penalty

        # BRAIN influence global
        if brain:
            for strategy, score in brain.strategy_score.items():
                for item in ranking.values():
                    item["score"] += score * 0.02

        return sorted(ranking.items(), key=lambda x: x[1]["score"], reverse=True)

    # =========================================================
    # HELPERS
    # =========================================================

    def _overlap(self, text: str, tag: str) -> float:
        text = text.lower()
        tag = tag.lower()

        if tag in text:
            return 1.0

        common = set(text.split()) & set(tag.split())
        return len(common) / (len(tag.split()) + 1)

    def _load(self, path: str):
        row = self.storage.fetchone("""
            SELECT content FROM files_index WHERE path = ?
        """, (path,))
        return row[0] if row else ""

    def _resolve(self, key: str):
        row = self.storage.fetchone("""
            SELECT file_path FROM file_tags WHERE tag = ? LIMIT 1
        """, (key,))
        return row[0] if row else None