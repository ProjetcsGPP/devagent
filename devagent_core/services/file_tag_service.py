from devagent_core.models.file_tag import FileTag


class FileTagService:
    """
    WRITE MODEL dos file_tags.
    Responsável por mutações no estado.
    """

    def __init__(self, storage):
        self.storage = storage

    # =========================================================
    # UPDATE WEIGHT
    # =========================================================
    def update_weight(self, file_path: str, tag: str, delta: float):

        self.storage.execute("""
            UPDATE file_tags
               SET weight = weight + ?
             WHERE file_path = ? AND tag = ?
        """, (delta, file_path, tag))

    # =========================================================
    # UPSERT TAG
    # =========================================================
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

    # =========================================================
    # DELETE BY FILE
    # =========================================================
    def delete_by_file(self, file_path: str):

        self.storage.execute("""
            DELETE FROM file_tags WHERE file_path = ?
        """, (file_path,))