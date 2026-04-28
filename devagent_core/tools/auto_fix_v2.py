from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Optional

from devagent_core.tools.test_tool import TestTool
from devagent_core.tools.edit_tool import EditTool


@dataclass
class AutoFixV2Result:
    success: bool
    attempts: int
    last_error: str = ""
    summary: str = ""


class AutoFixV2:
    def __init__(self, llm_service, edit_tool, test_tool, max_attempts: int = 3):
        self.llm = llm_service
        self.edit_tool = edit_tool
        self.test_tool = test_tool
        self.max_attempts = max_attempts

    def execute(self, target: str = ".") -> AutoFixV2Result:
        attempts = 0
        last_error = ""

        while attempts < self.max_attempts:
            attempts += 1

            test_result = self.test_tool.execute(target)

            if test_result.success:
                return AutoFixV2Result(
                    success=True,
                    attempts=attempts,
                    summary="Todos os testes passaram após auto-fix v2."
                )

            last_error = test_result.stderr or test_result.error or "Erro desconhecido"

            file_path = self._extract_file(last_error)

            if not file_path:
                return AutoFixV2Result(
                    success=False,
                    attempts=attempts,
                    last_error=last_error,
                    summary="Não foi possível identificar arquivo afetado."
                )

            instruction = self._build_llm_instruction(last_error, file_path)

            self.edit_tool.execute(
                file_path=file_path,
                instruction=instruction,
            )

        return AutoFixV2Result(
            success=False,
            attempts=attempts,
            last_error=last_error,
            summary="Máximo de tentativas atingido."
        )

    def _extract_file(self, error_text: str) -> Optional[str]:
        match = re.search(r'File "([^"]+\.py)"', error_text)
        return match.group(1) if match else None

    def _build_llm_instruction(self, error: str, file_path: str) -> str:
        prompt = f"""
Você é um engenheiro de software especialista em debugging.

Arquivo com erro:
{file_path}

Erro de execução/teste:
{error}

Tarefa:
- identifique a causa raiz
- proponha correção mínima
- mantenha compatibilidade com o restante do sistema
- evite refatorações desnecessárias

Responda apenas com a instrução de correção para o código.
"""

        return self.llm.generate(prompt)