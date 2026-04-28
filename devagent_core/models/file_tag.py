from dataclasses import dataclass
from typing import Optional
from datetime import datetime


@dataclass(slots=True)
class FileTag:
    file_path: str
    tag: str
    tag_type: str = "generic"   # generic | context | intent | domain | error | fix | execution
    weight: float = 1.0
    confidence: float = 0.5
    source: str = "indexer"     # indexer | llm | user | auto_fix
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    def ensure_timestamps(self):
        now = datetime.utcnow().isoformat()
        if not self.created_at:
            self.created_at = now
        self.updated_at = now