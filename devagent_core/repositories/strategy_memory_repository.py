import time


class StrategyMemoryRepository:
    def __init__(self, storage):
        self.storage = storage

    # =========================================================
    # LOAD RAW STATE (OK)
    # =========================================================
    def load_all(self) -> dict:
        rows = self.storage.fetchall("""
            SELECT
                strategy_name,
                score,
                success_count,
                failure_count,
                last_used,
                updated_at
            FROM strategy_memory
        """)

        return {
            r["strategy_name"]: {
                "strategy_name": r["strategy_name"],
                "score": r["score"],
                "success_count": r["success_count"],
                "failure_count": r["failure_count"],
                "last_used": r["last_used"],
                "updated_at": r["updated_at"],
            }
            for r in rows
        }

    # =========================================================
    # WRITE ONLY (SEM LÓGICA)
    # =========================================================
    def register_success(self, strategy: str):
        now = time.time()

        self.storage.execute("""
            UPDATE strategy_memory
               SET success_count = success_count + 1,
                   last_used = ?,
                   updated_at = ?
             WHERE strategy_name = ?
        """, (now, now, strategy))

    def register_failure(self, strategy: str):
        now = time.time()

        self.storage.execute("""
            UPDATE strategy_memory
               SET failure_count = failure_count + 1,
                   last_used = ?,
                   updated_at = ?
             WHERE strategy_name = ?
        """, (now, now, strategy))