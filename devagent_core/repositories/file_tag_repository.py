from typing import List
from devagent_core.models.file_tag import FileTag


class FileTagRepository:
    """
    READ MODEL PURO
    Somente leitura do estado persistido.
    """

    def __init__(self, storage):
        self.storage = storage

    # =========================================================
    # GET BY FILE
    # =========================================================
    def get_by_file(self, file_path: str) -> List[FileTag]:

        rows = self.storage.fetchall("""
            SELECT file_path, tag, tag_type, weight, confidence, source, created_at, updated_at
            FROM file_tags
            WHERE file_path = ?
        """, (file_path,))

        return [FileTag(*row) for row in rows]

    # =========================================================
    # SEARCH BY TAG
    # =========================================================
    def search_by_tag(self, tag: str) -> List[FileTag]:

        rows = self.storage.fetchall("""
            SELECT file_path, tag, tag_type, weight, confidence, source, created_at, updated_at
            FROM file_tags
            WHERE tag = ?
        """, (tag,))

        return [FileTag(*row) for row in rows]

    # =========================================================
    # GET ALL (USO CONTROLADO NO MIL)
    # =========================================================
    def get_all(self) -> List[FileTag]:

        rows = self.storage.fetchall("""
            SELECT file_path, tag, tag_type, weight, confidence, source, created_at, updated_at
            FROM file_tags
        """)

        return [FileTag(*row) for row in rows]