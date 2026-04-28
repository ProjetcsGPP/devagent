from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from devagent_core.tools.test_result import TestResult

__test__ = False


class TestTool:
    def execute(self, target: str = ".", timeout: int = 300) -> TestResult:
        path = Path(target).expanduser().resolve()

        if not path.exists():
            return TestResult(
                success=False,
                command=target,
                return_code=-1,
                error=f"Caminho não encontrado: {target}",
            )

        try:
            if self._has_pytest():
                command = [
                    sys.executable,
                    "-m",
                    "pytest",
                    str(path),
                    "-q",
                    "--rootdir=.",
                ]
            else:
                command = [
                    sys.executable,
                    "-m",
                    "unittest",
                    "discover",
                    str(path),
                ]

            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=timeout,
            )

            return TestResult(
                success=result.returncode == 0,
                command=" ".join(command),
                return_code=result.returncode,
                stdout=result.stdout,
                stderr=result.stderr,
            )

        except subprocess.TimeoutExpired:
            return TestResult(
                success=False,
                command=target,
                return_code=-1,
                error=f"Timeout de {timeout}s excedido",
            )

        except Exception as exc:
            return TestResult(
                success=False,
                command=target,
                return_code=-1,
                error=str(exc),
            )

    def _has_pytest(self) -> bool:
        try:
            subprocess.run(
                [sys.executable, "-m", "pytest", "--version"],
                capture_output=True,
                text=True,
                check=True,
            )
            return True
        except Exception:
            return False