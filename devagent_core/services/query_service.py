class QueryService:
    def __init__(self, storage):
        self.storage = storage

    # =========================================================
    # UTILITY
    # =========================================================
    def _dict(self, row):
        return dict(row) if row else None

    def _dict_list(self, rows):
        return [dict(r) for r in rows]


    def normalize(self, text: str):
        return (
            text.lower()
            .replace("_", "")
            .replace("-", "")
            .replace(".py", "")
        )

    # =========================================================
    # RAG
    # =========================================================
    def search_files(self, query: str, limit: int = 20):

        query = self.normalize(query)
        
        rows = self.storage.fetchall("""
            SELECT path, content
            FROM files_index
            WHERE LOWER(path) LIKE LOWER(?)
                OR LOWER(content) LIKE LOWER(?)
            LIMIT ?
        """, (
            f"%{query}%",
            f"%{query}%",
            limit
        ))

        return [
            {
                "path": r["path"],
                "content": r["content"]
            }
            for r in rows
        ]

    # =========================================================
    # TAGS
    # =========================================================
    def get_all_file_tags(self):
        rows = self.storage.fetchall("""
            SELECT file_path, tag, weight, confidence
            FROM file_tags
        """)
        return [
            {
                "file_path": r["file_path"],
                "tag": r["tag"],
                "weight": r["weight"],
                "confidence": r["confidence"],
            }
            for r in rows
        ]

    def find_file_by_tag(self, tag: str):
        rows = self.storage.fetchall("""
            SELECT file_path
            FROM file_tags
            WHERE tag = ?
            LIMIT 1
        """, (tag,))

        data = self._dict_list(rows)
        return data

    def get_file_tags_by_file(self, file_path: str):
        rows = self.storage.fetchall("""
            SELECT file_path, tag, weight, confidence
            FROM file_tags
            WHERE file_path = ?
        """, (file_path,))

        return self._dict_list(rows)

    def search_file_tags(self, tag: str):
        rows = self.storage.fetchall("""
            SELECT file_path, tag, weight, confidence
            FROM file_tags
            WHERE tag = ?
        """, (tag,))

        return [
            {
                "file_path": r["file_path"],
                "tag": r["tag"],
                "weight": r["weight"],
                "confidence": r["confidence"],
            }
            for r in rows
        ]

    # =========================================================
    # EXECUTION MEMORY
    # =========================================================
    def get_execution_events(self, limit: int = 300):
        rows = self.storage.fetchall("""
            SELECT data
            FROM memory_store
            WHERE type = 'execution'
            ORDER BY timestamp DESC
            LIMIT ?
        """, (limit,))

        return [dict(r) for r in rows]