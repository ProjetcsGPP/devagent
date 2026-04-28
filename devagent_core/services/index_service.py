import os
import json
from pathlib import Path
from typing import List
from devagent_core.models.file_tag import FileTag


class IndexService:
    def __init__(self, storage, file_tag_repo=None, llm=None):
        self.storage = storage
        self.file_tag_repo = file_tag_repo
        self.llm = llm  # 🔥 novo: LLM opcional

    # -------------------------
    # INDEX FILE
    # -------------------------
    def index_file(self, file_path: str):
        path = Path(file_path).resolve()

        if not path.exists() or not path.is_file():
            raise FileNotFoundError(file_path)

        content = path.read_text(encoding="utf-8", errors="ignore")

        # salva conteúdo
        self.storage.execute("""
            INSERT OR REPLACE INTO files_index (path, content)
            VALUES (?, ?)
        """, (str(path), content))

        # gera tags v2.1 (LLM + fallback)
        tags = self._generate_tags_v2_1(str(path), content)

        if self.file_tag_repo:
            for tag in tags:
                self.file_tag_repo.add(tag)

        return len(tags)

    # -------------------------
    # INDEX DIRECTORY
    # -------------------------
    def index_directory(self, directory: str):
        count = 0

        for root, _, files in os.walk(directory):
            for file in files:
                if file.endswith(".py"):
                    self.index_file(os.path.join(root, file))
                    count += 1

        return count

    # =========================================================
    # 🧠 TAG ENGINE v2.1 (LLM + FALLBACK)
    # =========================================================
    def _generate_tags_v2_1(self, file_path: str, content: str) -> List[FileTag]:

        # 1. tenta LLM primeiro
        if self.llm:
            llm_tags = self._llm_generate_tags(file_path, content)
            if llm_tags:
                return llm_tags

        # 2. fallback heurístico
        return self._heuristic_tags(file_path, content)

    # -------------------------
    # LLM TAG GENERATION
    # -------------------------
    def _llm_generate_tags(self, file_path: str, content: str) -> List[FileTag]:
        try:
            prompt = f"""
Você é um sistema de análise de código.

Analise o arquivo abaixo e gere tags semânticas.

REGRAS:
- responda APENAS em JSON válido
- no máximo 8 tags
- cada tag deve ter:
  - tag
  - tag_type (context | domain | intent | error | fix | execution)
  - weight (0.0 a 1.0)
  - confidence (0.0 a 1.0)

ARQUIVO:
{file_path}

CÓDIGO:
{content[:4000]}

FORMATO:
[
  {{
    "tag": "...",
    "tag_type": "...",
    "weight": 1.0,
    "confidence": 0.9
  }}
]
"""

            result = self.llm.generate(prompt)

            data = json.loads(result)

            tags = []

            for item in data:
                tags.append(
                    FileTag(
                        file_path=file_path,
                        tag=item.get("tag"),
                        tag_type=item.get("tag_type", "generic"),
                        weight=float(item.get("weight", 1.0)),
                        confidence=float(item.get("confidence", 0.5)),
                        source="llm"
                    )
                )

            return tags

        except Exception:
            return []

    # -------------------------
    # FALLBACK HEURÍSTICO
    # -------------------------
    def _heuristic_tags(self, file_path: str, content: str) -> List[FileTag]:
        tags: List[FileTag] = []
        lower = content.lower()

        if "bootstrap" in lower:
            tags.append(FileTag(file_path, "bootstrap", "context", 1.0, 0.9, "heuristic"))

        if "rag" in lower:
            tags.append(FileTag(file_path, "rag", "domain", 1.0, 0.95, "heuristic"))

        if "llm" in lower or "ollama" in lower:
            tags.append(FileTag(file_path, "llm", "domain", 1.0, 0.9, "heuristic"))

        if "subprocess" in lower:
            tags.append(FileTag(file_path, "execution", "intent", 1.0, 0.9, "heuristic"))

        if "test" in lower:
            tags.append(FileTag(file_path, "test", "domain", 1.0, 0.9, "heuristic"))

        if "error" in lower or "exception" in lower:
            tags.append(FileTag(file_path, "error_handling", "context", 0.8, 0.85, "heuristic"))

        if "class " in lower:
            tags.append(FileTag(file_path, "oop", "context", 0.7, 0.7, "heuristic"))

        if not tags:
            tags.append(FileTag(file_path, "general", "generic", 0.3, 0.5, "heuristic"))

        return tags