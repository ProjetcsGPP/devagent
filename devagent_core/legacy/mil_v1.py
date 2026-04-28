from collections import defaultdict
import sqlite3
import math


class MILv1:
    """
    Memory Intelligence Layer v1
    - ranking de contexto
    - uso de tags
    - aprendizado de relevância
    """

    def __init__(self, storage):
        self.db = storage.connection

    # =========================================================
    # STORE EVENT
    # =========================================================
    def store_event(self, event: dict):
        self.db.execute("""
            INSERT INTO memory_events (
                type, intent, strategy, plan,
                success, error_type, timestamp
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            event.get("type"),
            str(event.get("intent")),
            event.get("strategy"),
            str(event.get("plan")),
            int(event.get("success", 0)),
            event.get("error_type"),
            event.get("timestamp"),
        ))
        self.db.commit()

    # =========================================================
    # TAGGING (FILE)
    # =========================================================
    def tag_file(self, file_path: str, tag: str, weight: float = 1.0):

        self.db.execute("""
            INSERT INTO file_tags (file_path, tag, weight)
            VALUES (?, ?, ?)
        """, (file_path, tag, weight))

        self.db.commit()

    # =========================================================
    # TAGGING (ENTITY)
    # =========================================================
    def tag_entity(self, entity: str, tag: str, weight: float = 1.0):

        self.db.execute("""
            INSERT INTO entity_tags (entity, tag, weight)
            VALUES (?, ?, ?)
        """, (entity, tag, weight))

        self.db.commit()

    # =========================================================
    # CONTEXT RANKING ENGINE
    # =========================================================
    def get_relevant_context(self, intent: str, limit: int = 10):

        rows = self.db.execute("""
            SELECT intent, strategy, success, error_type, timestamp
            FROM memory_events
            ORDER BY timestamp DESC
            LIMIT 200
        """).fetchall()

        scored = []

        for r in rows:

            score = 0.0

            # match simples de intent
            if r[0] and intent in r[0]:
                score += 2.0

            # sucesso pesa mais
            if r[2] == 1:
                score += 1.5
            else:
                score -= 1.0

            # estratégia repetida ajuda aprendizado
            if r[1]:
                score += 0.5

            scored.append((score, r))

        scored.sort(reverse=True, key=lambda x: x[0])

        return scored[:limit]

    # =========================================================
    # STRATEGY PREDICTION
    # =========================================================
    def best_strategy(self, intent: str):

        rows = self.get_relevant_context(intent, limit=20)

        counter = defaultdict(float)

        for score, r in rows:
            strategy = r[1]
            success = r[2]

            if not strategy:
                continue

            if success:
                counter[strategy] += score
            else:
                counter[strategy] -= score

        if not counter:
            return None

        return max(counter.items(), key=lambda x: x[1])[0]

    # =========================================================
    # ERROR PATTERN ANALYSIS
    # =========================================================
    def most_common_error(self, intent: str):

        rows = self.db.execute("""
            SELECT error_type, COUNT(*)
            FROM memory_events
            WHERE error_type IS NOT NULL
            GROUP BY error_type
            ORDER BY COUNT(*) DESC
        """).fetchall()

        if not rows:
            return None

        return rows[0][0]