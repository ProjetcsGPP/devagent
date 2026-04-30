from dataclasses import dataclass
from typing import Dict, List, Optional
import time


@dataclass
class EventContractV1:
    type: str
    timestamp: float
    success: bool
    intent: Dict
    strategy: str
    plan: List
    error: Optional[str] = None
    metadata: Optional[Dict] = None

    @staticmethod
    def create(
        type: str,
        intent: Dict,
        strategy: str,
        plan: List,
        success: bool = True,
        error: Optional[str] = None,
        metadata: Optional[Dict] = None,
    ):
        return EventContractV1(
            type=type,
            timestamp=time.time(),
            success=success,
            intent=intent,
            strategy=strategy,
            plan=plan,
            error=error,
            metadata=metadata or {},
        )