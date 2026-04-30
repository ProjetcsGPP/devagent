import os
import json
from pathlib import Path
from typing import List
from devagent_core.models.file_tag import FileTag


class IndexServiceV2_1:
    def __init__(self, storage, llm_service, file_tag_service):
        self.storage = storage
        self.llm = llm_service
        self.tags = file_tag_service

    # =====================================================
    def index_file(self, path: str):

        content = self._read_file(path)

        if not content:
            return 0

        self._store_file_index(path, content)

        tags = self._generate_tags(path, content)

        self._store_tags(path, tags)

        return len(tags)

    # =====================================================
    def index_directory(self, directory: str):

        count = 0

        for root, _, files in os.walk(directory):
            for f in files:
                if f.endswith(".py"):
                    count += self.index_file(os.path.join(root, f))

        return count

    # =====================================================
    def _store_file_index(self, path: str, content: str):

        self.storage.execute(
            """
            INSERT OR REPLACE INTO files_index (path, content)
            VALUES (?, ?)
            """,
            (path, content),
        )

    # =====================================================
    def _generate_tags(self, path: str, content: str) -> List[FileTag]:

        tags = self._llm_tags(path, content)

        if not tags:
            tags = self._heuristic_tags(path, content)

        return tags

    # =====================================================
    def _llm_tags(self, path: str, content: str):

        prompt = f"""
Gere tags para este arquivo.

RETORNE JSON:

[
  {{
    "tag": "api",
    "tag_type": "architecture",
    "weight": 2.0,
    "confidence": 0.9
  }}
]

ARQUIVO:
{path}

CONTEÚDO:
{content[:4000]}
"""

        try:
            data = self.llm.generate_json(prompt)

            if not isinstance(data, list):
                return []

            return [
                FileTag(
                    file_path=path,
                    tag=item.get("tag"),
                    tag_type=item.get("tag_type", "generic"),
                    weight=float(item.get("weight", 1.0)),
                    confidence=float(item.get("confidence", 0.5)),
                    source="llm"
                )
                for item in data if isinstance(item, dict)
            ]

        except Exception:
            return []

    # =====================================================
    def _heuristic_tags(self, path: str, content: str) -> List[FileTag]:

        text = (path + content).lower()
        tags = []

        def add(tag, tag_type="heuristic", weight=1.0, confidence=0.6):
            tags.append(FileTag(
                file_path=path,
                tag=tag,
                tag_type=tag_type,
                weight=weight,
                confidence=confidence,
                source="heuristic",
            ))

        if "test" in text:
            add("testing", "quality", 2.0)

        if "api" in text:
            add("api", "architecture", 2.0)

        if "sql" in text:
            add("database", "data", 2.0)

        return tags

    # =====================================================
    def _store_tags(self, path: str, tags: List[FileTag]):

        self.tags.delete_by_file(path)

        for tag in tags:
            tag.file_path = path
            self.tags.add(tag)

    # =====================================================
    def _read_file(self, path: str):
        try:
            return Path(path).read_text(encoding="utf-8")
        except Exception:
            return None