"""
dev_agent/tools/shell.py

Execução segura de comandos shell.
"""

from __future__ import annotations

import shlex
import subprocess
from typing import List

from dev_agent.config import ALLOWED_SHELL_COMMANDS
from dev_agent.tools.base import Tool


class ShellTool(Tool):
    """
    Ferramenta para execução segura de comandos shell.
    """

    name = "shell"
    description = "Executa comandos Linux permitidos"

    def execute(self, *args, **kwargs) -> str:
        """
        Executa um comando shell autorizado.
        """
        command = kwargs.get("command")

        # Caso o registry envie um dicionário posicional
        if command is None and args:
            first = args[0]

            if isinstance(first, dict):
                command = first.get("command")
            else:
                command = first

        if not command:
            return "Nenhum comando informado."

        command = str(command).strip()

        try:
            parts: List[str] = shlex.split(command)
        except ValueError as exc:
            return f"Erro de sintaxe: {exc}"

        executable = parts[0]

        if executable not in ALLOWED_SHELL_COMMANDS:
            return (
                f"Comando não permitido: '{executable}'.\n"
                f"Use apenas comandos autorizados."
            )

        try:
            result = subprocess.run(
                parts,
                capture_output=True,
                text=True,
                timeout=120,
                check=False,
            )

            output = result.stdout.strip()
            error = result.stderr.strip()

            if result.returncode != 0:
                return error or (
                    f"Comando finalizado com código "
                    f"{result.returncode}."
                )

            return output or "Comando executado com sucesso."

        except subprocess.TimeoutExpired:
            return "Tempo limite excedido."

        except Exception as exc:
            return f"Erro ao executar comando: {exc}"