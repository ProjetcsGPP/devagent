import os
from typing import List

from devagent_core.models.file_tag import FileTag


class IndexServiceV2_1:
    """
    Indexador cognitivo:
    - indexa arquivos
    - gera tags via LLM
    - fallback heurístico
    - persiste via FileTagRepository (CORRETO)
    """

    def __init__(self, storage, llm_service, file_tag_repository):
        self.storage = storage
        self.llm = llm_service
        self.tags = file_tag_repository

    # =========================================================
    # ENTRY POINT
    # =========================================================
    def index_file(self, path: str):

        content = self._read_file(path)

        if not content:
            return 0

        self._store_file_index(path, content)

        tags = self._generate_tags(path, content)

        self._store_tags(path, tags)

        return 1

    # =========================================================
    # DIRECTORY INDEX
    # =========================================================
    def index_directory(self, directory: str):

        count = 0

        for root, _, files in os.walk(directory):

            for f in files:

                if not f.endswith(".py"):
                    continue

                count += self.index_file(os.path.join(root, f))

        return count

    # =========================================================
    # FILE STORAGE
    # =========================================================
    def _store_file_index(self, path: str, content: str):

        self.storage.execute(
            """
            INSERT OR REPLACE INTO files_index (path, content)
            VALUES (?, ?)
            """,
            (path, content),
        )

    # =========================================================
    # TAG GENERATION PIPELINE
    # =========================================================
    def _generate_tags(self, path: str, content: str) -> List[FileTag]:

        tags = self._llm_tags(path, content)

        if not tags:
            tags = self._heuristic_tags(path, content)

        return tags

    # =========================================================
    # LLM TAGGING
    # =========================================================
    def _llm_tags(self, path: str, content: str):

        prompt = f"""
Gere tags para este arquivo.

RETORNE SOMENTE JSON:

[
  {{
    "tag": "api",
    "tag_type": "architecture",
    "weight": 2.0,
    "confidence": 0.9
  }}
]

REGRAS:
- máximo 6 tags
- use termos técnicos reais
- evite genéricos

ARQUIVO:
{path}

CONTEÚDO:
{content[:4000]}
"""

        try:
            data = self.llm.generate_json(prompt)

            return data if isinstance(data, list) else []

        except Exception:
            return []

    # =========================================================
    # FALLBACK HEURÍSTICO
    # =========================================================
    def _heuristic_tags(self, path: str, content: str) -> List[FileTag]:

        text = (path + content).lower()
        tags = []

        def add(tag, tag_type="heuristic", weight=1.0, confidence=0.6):
            tags.append(
                FileTag(
                    file_path=path,
                    tag=tag,
                    tag_type=tag_type,
                    weight=weight,
                    confidence=confidence,
                    source="heuristic",
                )
            )

        if "test" in text:
            add("testing", "quality", 2.0)

        if "router" in text:
            add("routing", "architecture", 2.0)

        if "sql" in text or "select" in text:
            add("database", "data", 2.0)

        if "class" in text:
            add("oop", "structure", 1.0)

        if "api" in text:
            add("api", "architecture", 2.0)

        return tags

    # =========================================================
    # STORE TAGS (USANDO SEU REPOSITORY REAL)
    # =========================================================
    def _store_tags(self, path: str, tags: List[FileTag]):

        # limpa tags antigas (evita drift)
        self.tags.delete_by_file(path)

        for tag in tags:

            # garante path correto
            tag.file_path = path

            self.tags.add(tag)

    # =========================================================
    # FILE READING
    # =========================================================
    def _read_file(self, path: str):

        try:
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception:
            return None