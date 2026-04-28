from __future__ import annotations

"""
DevAgent - Edit Tool

Implementa edição assistida por LLM com:
- backup automático
- sobrescrita segura
- diff resumido
- base preparada para rollback futuro
"""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import difflib
import shutil
from typing import Optional


@dataclass(slots=True)
class EditResult:
    success: bool
    file_path: str
    instruction: str
    summary: str
    diff: str
    backup_path: Optional[str] = None
    message: str = ""
    error: Optional[str] = None


class EditTool:
    """Ferramenta de edição assistida por LLM."""

    def __init__(self, llm_service, backup_dir: str = ".devagent/backups"):
        self.llm = llm_service
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    def execute(self, file_path: str, instruction: str) -> EditResult:
        """Executa a edição de um arquivo."""
        path = Path(file_path)

        if not path.exists():
            return EditResult(
                success=False,
                file_path=file_path,
                backup_path=None,
                instruction=instruction,
                summary="Arquivo não encontrado.",
                diff="",
                error=f"Arquivo inexistente: {file_path}",
            )

        try:
            original_content = path.read_text(encoding="utf-8")

            new_content = self._generate_edited_content(
                original_content,
                instruction,
                str(path),
            )

            if new_content.strip() == original_content.strip():
                return EditResult(
                    success=True,
                    file_path=str(path),
                    backup_path=None,
                    instruction=instruction,
                    summary="Nenhuma alteração foi necessária.",
                    diff="",
                )

            backup_path = self._create_backup(path)
            self._safe_write(path, new_content)

            diff = self._generate_diff(
                original_content,
                new_content,
                str(path),
            )

            return EditResult(
                success=True,
                file_path=str(path),
                backup_path=str(backup_path),
                instruction=instruction,
                summary=self._summarize_diff(diff),
                diff=diff,
            )

        except Exception as exc:  # pragma: no cover
            return EditResult(
                success=False,
                file_path=str(path),
                backup_path=None,
                instruction=instruction,
                summary="Falha durante a edição.",
                diff="",
                error=str(exc),
            )

    def _generate_edited_content(
        self,
        original_content: str,
        instruction: str,
        file_path: str,
    ) -> str:
        prompt = f"""
Você é um engenheiro de software especialista em refatoração.

Arquivo: {file_path}

Instrução do usuário:
{instruction}

Regras obrigatórias:
- Preserve a funcionalidade existente.
- Retorne SOMENTE o código completo atualizado.
- Não utilize markdown.
- Não adicione explicações.
- Mantenha estilo Python limpo e profissional.

Código atual:
{original_content}
""".strip()

        updated_content = self.llm.generate(prompt)
        response = self._clean_response(updated_content)
        return response.strip()

    def _create_backup(self, file_path: Path) -> Path:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{file_path.name}.{timestamp}.bak"
        backup_path = self.backup_dir / backup_name

        shutil.copy2(file_path, backup_path)
        return backup_path

    def _safe_write(self, file_path: Path, content: str) -> None:
        temp_path = file_path.with_suffix(file_path.suffix + ".tmp")

        temp_path.write_text(content, encoding="utf-8")
        temp_path.replace(file_path)

    def _generate_diff(
        self,
        original: str,
        updated: str,
        file_path: str,
    ) -> str:
        diff_lines = difflib.unified_diff(
            original.splitlines(),
            updated.splitlines(),
            fromfile=f"{file_path} (original)",
            tofile=f"{file_path} (updated)",
            lineterm="",
        )
        return "\n".join(diff_lines)

    def _summarize_diff(self, diff_text: str) -> str:
        added = 0
        removed = 0

        for line in diff_text.splitlines():
            if line.startswith("+++") or line.startswith("---"):
                continue
            if line.startswith("+"):
                added += 1
            elif line.startswith("-"):
                removed += 1

        return (
            f"Edição concluída com sucesso: "
            f"{added} linha(s) adicionada(s), "
            f"{removed} linha(s) removida(s)."
        )

    def _clean_response(self, content: str) -> str:
        """
        Remove blocos Markdown retornados pelo LLM.
        """
        content = content.strip()

        if content.startswith("```"):
            lines = content.splitlines()

            if lines and lines[0].startswith("```"):
                lines = lines[1:]

            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]

            content = "\n".join(lines)

        return content.strip()