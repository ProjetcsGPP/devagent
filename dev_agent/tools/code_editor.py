"""
dev_agent/tools/code_editor.py

Editor automático de código.
"""

from __future__ import annotations

from pathlib import Path

from dev_agent.tools.base import Tool


class CodeEditorTool(Tool):
    """
    Ferramenta para edição automática de arquivos.
    """

    name = "edit"
    description = "Edita arquivos aplicando substituições"

    def execute(self, action: str, *args: str) -> str:
        if action == "replace":
            if len(args) < 3:
                return "Uso: @edit replace <arquivo> <buscar> <substituir>"
            return self._replace(args[0], args[1], args[2])

        if action == "append":
            if len(args) < 2:
                return "Uso: @edit append <arquivo> <texto>"

            filename = args[0]
            text = " ".join(args[1:])  # <- CORREÇÃO IMPORTANTE
            return self._append(filename, text)

        if action == "prepend":
            if len(args) < 2:
                return "Uso: @edit prepend <arquivo> <texto>"

            filename = args[0]
            text = " ".join(args[1:])  # <- CORREÇÃO IMPORTANTE
            return self._prepend(filename, text)

        return (
            "Uso:\n"
            "@edit replace <arquivo> <buscar> <substituir>\n"
            "@edit append <arquivo> <texto>\n"
            "@edit prepend <arquivo> <texto>"
        )
    
    # -------------------------
    # Replace
    # -------------------------

    def _replace(self, filename: str, old: str, new: str) -> str:
        path = Path(filename)

        if not path.exists():
            return f"Arquivo não encontrado: {filename}"

        content = path.read_text(
            encoding="utf-8",
            errors="ignore",
        )

        if old not in content:
            return "Texto não encontrado."

        updated = content.replace(old, new)

        path.write_text(updated, encoding="utf-8")

        return f"Arquivo atualizado: {filename}"

    # -------------------------
    # Append
    # -------------------------

    def _append(self, filename: str, text: str) -> str:
        path = Path(filename)

        text = text.replace("\\n", "\n")

        current = ""
        if path.exists():
            current = path.read_text(
                encoding="utf-8",
                errors="ignore",
            )

        if current and not current.endswith("\n"):
            current += "\n"

        path.write_text(
            current + text,
            encoding="utf-8",
        )

        return f"Texto adicionado ao final de {filename}"

    # -------------------------
    # Prepend
    # -------------------------

    def _prepend(self, filename: str, text: str) -> str:
        path = Path(filename)

        text = text.replace("\\n", "\n")

        current = ""
        if path.exists():
            current = path.read_text(
                encoding="utf-8",
                errors="ignore",
            )

        path.write_text(
            text + current,
            encoding="utf-8",
        )

        return f"Texto adicionado ao início de {filename}"