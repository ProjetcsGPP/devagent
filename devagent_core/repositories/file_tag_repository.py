from typing import List, Optional
from devagent_core.models.file_tag import FileTag


class FileTagRepository:
    def __init__(self, storage):
        self.storage = storage

        self._init_table()

    def _init_table(self):
        self.storage.execute("""
        CREATE TABLE IF NOT EXISTS file_tags (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_path TEXT NOT NULL,
            tag TEXT NOT NULL,
            tag_type TEXT DEFAULT 'generic',
            weight REAL DEFAULT 1.0,
            confidence REAL DEFAULT 0.5,
            source TEXT DEFAULT 'indexer',
            created_at TEXT,
            updated_at TEXT,
            UNIQUE(file_path, tag)
        )
        """)

    # -------------------------
    # CREATE / UPSERT
    # -------------------------
    def add(self, tag: FileTag):
        tag.ensure_timestamps()

        self.storage.execute("""
        INSERT OR REPLACE INTO file_tags (
            file_path, tag, tag_type, weight, confidence,
            source, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            tag.file_path,
            tag.tag,
            tag.tag_type,
            tag.weight,
            tag.confidence,
            tag.source,
            tag.created_at,
            tag.updated_at,
        ))

    # -------------------------
    # GET BY FILE
    # -------------------------
    def get_by_file(self, file_path: str) -> List[FileTag]:
        rows = self.storage.fetchall("""
            SELECT file_path, tag, tag_type, weight, confidence, source, created_at, updated_at
            FROM file_tags
            WHERE file_path = ?
        """, (file_path,))

        return [FileTag(*row) for row in rows]

    # -------------------------
    # SEARCH BY TAG
    # -------------------------
    def search_by_tag(self, tag: str) -> List[FileTag]:
        rows = self.storage.fetchall("""
            SELECT file_path, tag, tag_type, weight, confidence, source, created_at, updated_at
            FROM file_tags
            WHERE tag = ?
            ORDER BY weight DESC, confidence DESC
        """, (tag,))

        return [FileTag(*row) for row in rows]

    # -------------------------
    # DELETE FILE TAGS
    # -------------------------
    def delete_by_file(self, file_path: str):
        self.storage.execute("""
            DELETE FROM file_tags WHERE file_path = ?
        """, (file_path,))