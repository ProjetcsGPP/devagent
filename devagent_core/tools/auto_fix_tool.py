from __future__ import annotations

from dataclasses import dataclass
from typing import Optional
import re

from devagent_core.tools.test_tool import TestTool
from devagent_core.tools.edit_tool import EditTool


@dataclass
class AutoFixResult:
    success: bool
    attempts: int
    last_error: str = ""
    summary: str = ""


class AutoFixTool:
    def __init__(self, llm_service, max_attempts: int = 3):
        self.test_tool = TestTool()
        self.edit_tool = EditTool(llm_service)
        self.max_attempts = max_attempts

    def execute(self, target: str = ".") -> AutoFixResult:
        attempts = 0
        last_error = ""

        while attempts < self.max_attempts:
            attempts += 1

            test_result = self.test_tool.execute(target)

            if test_result.success:
                return AutoFixResult(
                    success=True,
                    attempts=attempts,
                    summary="Todos os testes passaram após auto-fix."
                )

            last_error = test_result.stderr or test_result.error or "Erro desconhecido"

            file_hint = self._extract_file(last_error)

            if not file_hint:
                return AutoFixResult(
                    success=False,
                    attempts=attempts,
                    last_error=last_error,
                    summary="Não foi possível identificar arquivo afetado."
                )

            instruction = self._build_instruction(last_error)

            self.edit_tool.execute(
                file_path=file_hint,
                instruction=instruction,
            )

        return AutoFixResult(
            success=False,
            attempts=attempts,
            last_error=last_error,
            summary="Máximo de tentativas atingido."
        )

    def _extract_file(self, error_text: str) -> Optional[str]:
        match = re.search(r'File "([^"]+\.py)"', error_text)
        return match.group(1) if match else None

    def _build_instruction(self, error_text: str) -> str:
        return f"""
Corrigir erro de teste baseado no stack trace abaixo:

{error_text}

Regras:
- manter funcionalidade existente
- corrigir apenas o necessário
- não quebrar outras partes do sistema
"""