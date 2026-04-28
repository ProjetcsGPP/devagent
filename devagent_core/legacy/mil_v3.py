from collections import defaultdict
import math


class MILv3:

    def __init__(self, storage):
        self.storage = storage

        self.tag_strength = defaultdict(float)
        self.file_strength = defaultdict(float)
        self.strategy_success = defaultdict(lambda: {"ok": 0, "fail": 0})

    def retrieve_context(self, query: str, tag_scores: dict, limit: int = 5):

        rag_results = self._rag_search(query, limit)
        merged = self._merge(rag_results, tag_scores)

        return self._build_context(merged)

    def _rag_search(self, query, limit):

        return self.storage.fetchall("""
            SELECT path, content
            FROM files_index
            WHERE content LIKE ?
            LIMIT ?
        """, (f"%{query}%", limit))

    def _merge(self, rag_results, tag_scores):

        ranking = {}

        # -------------------------
        # BASE RAG SCORE
        # -------------------------
        for path, content in rag_results:

            ranking[path] = {
                "content": content,
                "score": self.file_strength[path] + 1.0
            }

        # -------------------------
        # TAG BOOST + EVOLUTION
        # -------------------------
        for path, score in tag_scores.items():

            if path not in ranking:

                row = self.storage.fetchone(
                    "SELECT content FROM files_index WHERE path = ?",
                    (path,)
                )

                if not row:
                    continue

                ranking[path] = {
                    "content": row[0],
                    "score": 0.5
                }

            tag_boost = self._get_tag_boost(path)

            ranking[path]["score"] += score * tag_boost

        # ranking final
        return sorted(
            ranking.items(),
            key=lambda x: x[1]["score"],
            reverse=True
        )

    def _get_tag_boost(self, path: str):

        rows = self.storage.fetchall("""
            SELECT tag, weight
            FROM file_tags
            WHERE file_path = ?
        """, (path,))

        if not rows:
            return 1.0

        total = 0.0

        for tag, weight in rows:

            strength = self.tag_strength[tag]

            total += weight * (1.0 + strength)

        return 1.0 + (total * 0.1)

    def feedback(self, intent, plan, success: bool, used_paths: list, strategy: str):

        # -------------------------
        # STRATEGY LEARNING
        # -------------------------
        if success:
            self.strategy_success[strategy]["ok"] += 1
        else:
            self.strategy_success[strategy]["fail"] += 1

        # -------------------------
        # FILE LEARNING
        # -------------------------
        for path in used_paths:

            if success:
                self.file_strength[path] += 0.2
            else:
                self.file_strength[path] -= 0.3

        # -------------------------
        # TAG LEARNING
        # -------------------------
        tags = self._get_tags_for_paths(used_paths)

        for tag in tags:

            if success:
                self.tag_strength[tag] += 0.1
            else:
                self.tag_strength[tag] -= 0.2

    def _get_tags_for_paths(self, paths):

        tags = []

        for p in paths:

            rows = self.storage.fetchall(
                "SELECT tag FROM file_tags WHERE file_path = ?",
                (p,)
            )

            for r in rows:
                tags.append(r[0])

        return tags

    def best_strategy(self):

        if not self.strategy_success:
            return None

        return max(
            self.strategy_success.items(),
            key=lambda x: x[1]["ok"] - x[1]["fail"]
        )[0]

