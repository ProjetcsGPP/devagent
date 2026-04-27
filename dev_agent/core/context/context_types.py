from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class ContextItem:
    source: str          # memory | rag | project | session
    content: Any
    score: float
    metadata: Optional[Dict] = None