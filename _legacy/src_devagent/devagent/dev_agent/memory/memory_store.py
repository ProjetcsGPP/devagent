import json
import uuid
from pathlib import Path
from datetime import datetime
from typing import List, Dict
from devagent.core.llm import OllamaClient
import math 


class MemoryStore:
    def __init__(self, path: str = "dev_agent/memory/memory.json"):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

        if not self.path.exists():
            self.path.write_text("[]", encoding="utf-8")
        
        self.llm = OllamaClient()

    # --------------------------
    # IO
    # --------------------------

    def _load(self) -> List[Dict]:
        return json.loads(self.path.read_text(encoding="utf-8"))

    def _save(self, data: List[Dict]):
        self.path.write_text(
            json.dumps(data, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    # --------------------------
    # WRITE MEMORY
    # --------------------------

    def save(self, content: str, tags: List[str], source: str = "manual"):
        data = self._load()

        item = {
            "id": str(uuid.uuid4()),
            "content": content,
            "tags": tags,
            "source": source,
            "timestamp": datetime.utcnow().isoformat(),
            "embedding": self._embed(content),
        }

        data.append(item)
        self._save(data)

        return item

    def _embed(self, text: str):
        try:
            return self.llm.embeddings(text)
        except Exception:
            return []

    def _cosine_similarity(self, a, b):
        if not a or not b:
            return 0.0

        dot = sum(x * y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(x * x for x in b))

        if norm_a == 0 or norm_b == 0:
            return 0.0

        return dot / (norm_a * norm_b)

    def _tag_match(self, query: str, tags: List[str]) -> float:
        q = query.lower()

        if not tags:
            return 0.0

        for t in tags:
            if t.lower() in q:
                return 1.0

        return 0.0


    def _recency_score(self, timestamp: str) -> float:
        try:
            dt = datetime.fromisoformat(timestamp)
            age = (datetime.utcnow() - dt).days

            if age <= 1:
                return 1.0
            if age <= 7:
                return 0.7
            if age <= 30:
                return 0.4
            return 0.1

        except:
            return 0.0
    # --------------------------
    # SEARCH
    # --------------------------

    def search_by_tag(self, tag: str) -> List[Dict]:
        data = self._load()
        return [m for m in data if tag in m.get("tags", [])]

    def search_text(self, query: str, top_k: int = 5) -> List[Dict]:
        data = self._load()

        if not data:
            return []

        query_vec = self._embed(query)

        scored = []

        for m in data:
            sim = self._cosine_similarity(query_vec, m.get("embedding", []))
            tag_score = self._tag_match(query, m.get("tags", []))
            recency = self._recency_score(m.get("timestamp"))

            score = (sim * 0.7) + (tag_score * 0.2) + (recency * 0.1)

            scored.append((score, m))

        scored.sort(key=lambda x: x[0], reverse=True)

        return [m for _, m in scored[:top_k]]

    # --------------------------
    # TAGS
    # --------------------------

    def list_tags(self) -> List[str]:
        data = self._load()
        tags = set()

        for m in data:
            tags.update(m.get("tags", []))

        return sorted(tags)