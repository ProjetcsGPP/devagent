from __future__ import annotations

from dataclasses import dataclass
from typing import List, Dict, Any, Optional


@dataclass
class ContextPacket:
    """
    Representa o contexto consolidado do DevAgent.
    """

    user_input: str
    history: List[Dict[str, str]]
    rag: Optional[Dict[str, Any]] = None
    memory: Optional[Dict[str, Any]] = None
    project: Optional[Dict[str, Any]] = None

    def is_empty(self) -> bool:
        return (
            not self.history
            and not self.rag
            and not self.memory
            and not self.project
        )