# devagent_core/services/memory_service.py

import json
import time


class MemoryService:
    def __init__(self, storage):
        self.storage = storage

    def set(self, key, value):
        self.storage.execute(
            "INSERT OR REPLACE INTO memory_store (key, value) VALUES (?, ?)",
            (key, value)
        )

    def get(self, key):
        r = self.storage.fetchone(
            "SELECT value FROM memory_store WHERE key=?",
            (key,)
        )
        return r[0] if r else None

    # =========================
    # EVENT LOG (NOVA MEMÓRIA)
    # =========================
    def record_event(self, event: dict):
        self.storage.execute(
            """
            INSERT INTO memory_store (type, data, timestamp)
            VALUES (?, ?, ?)
            """,
            (
                event.get("type"),
                json.dumps(event),
                time.time()
            )
        )