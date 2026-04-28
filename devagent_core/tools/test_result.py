from dataclasses import dataclass
from typing import Optional

@dataclass(slots=True)
class TestResult:
    success: bool
    command: str
    return_code: int
    stdout: str = ""
    stderr: str = ""
    error: Optional[str] = None