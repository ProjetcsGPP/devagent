from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional
import re


@dataclass(slots=True)
class CodeResult:
    success: bool
    file_path: str
    generated_code: str
    summary: str
    error: Optional[str] = None


class CodeTool:
    def __init__(self, llm_service, workspace: str = "workspace"):
        self.llm = llm_service
        self.workspace = Path(workspace)
        self.workspace.mkdir(parents=True, exist_ok=True)

    def execute(self, prompt: str) -> CodeResult:
        filename = self._infer_filename(prompt)

        full_path = self.workspace / filename

        llm_prompt = f"""
Você é um engenheiro Python sênior.

Tarefa:
{prompt}

Regras obrigatórias:
- Gere código Python completo e executável.
- Retorne SOMENTE o código.
- Não use markdown.
- Não adicione explicações.
- Use boas práticas.

Código:
"""

        try:
            generated_code = self.llm.generate(llm_prompt)
            generated_code = self._clean_response(generated_code)

            full_path.write_text(
                generated_code,
                encoding="utf-8"
            )

            return CodeResult(
                success=True,
                file_path=str(full_path),
                generated_code=generated_code,
                summary=f"Arquivo criado: {full_path}"
            )

        except Exception as e:
            return CodeResult(
                success=False,
                file_path=str(full_path),
                generated_code="",
                summary="Falha na geração do código.",
                error=str(e)
            )

    def _infer_filename(self, prompt: str) -> str:
        text = prompt.lower()

        if "hello world" in text:
            return "hello_world.py"

        slug = re.sub(r"[^a-z0-9]+", "_", text).strip("_")
        slug = slug[:60] or "generated_script"

        return f"{slug}.py"

    def _clean_response(self, content: str) -> str:
        content = content.strip()

        if content.startswith("```"):
            lines = content.splitlines()

            if lines[0].startswith("```"):
                lines = lines[1:]

            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]

            content = "\n".join(lines)

        return content.strip()