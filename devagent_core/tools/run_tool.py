from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import subprocess
from typing import Optional


@dataclass(slots=True)
class RunResult:
    success: bool
    command: str
    return_code: int
    stdout: str = ""
    stderr: str = ""
    error: Optional[str] = None


class RunTool:
    def execute(
        self,
        target: str,
        timeout: int = 300,
    ) -> RunResult:
        path = Path(target).expanduser().resolve()

        if not path.exists():
            return RunResult(
                success=False,
                command=target,
                return_code=-1,
                error=f"Arquivo não encontrado: {target}",
            )

        try:
            command = ["python", str(path)]

            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=timeout,
            )

            return RunResult(
                success=result.returncode == 0,
                command=" ".join(command),
                return_code=result.returncode,
                stdout=result.stdout,
                stderr=result.stderr,
            )

        except subprocess.TimeoutExpired:
            return RunResult(
                success=False,
                command=target,
                return_code=-1,
                error=f"Tempo limite excedido ({timeout}s).",
            )

        except Exception as exc:
            return RunResult(
                success=False,
                command=target,
                return_code=-1,
                error=str(exc),
            )