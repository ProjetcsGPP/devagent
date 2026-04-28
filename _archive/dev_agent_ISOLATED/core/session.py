"""
dev_agent/core/session.py

Gerenciamento do histórico da conversa.
"""

from __future__ import annotations

from typing import Dict, List

from dev_agent.config import MAX_HISTORY
import json
from pathlib import Path


class SessionManager:
    """
    Mantém o histórico da conversa com limite configurável.
    """

    def __init__(self, max_history: int = MAX_HISTORY) -> None:
        self.max_history = max_history
        self.messages: List[Dict[str, str]] = []

    # ------------------------------------------------------------------
    # Manipulação de mensagens
    # ------------------------------------------------------------------

    def add_user_message(self, content: str) -> None:
        self.messages.append({
            "role": "user",
            "content": content,
        })
        self._trim()

    def add_assistant_message(self, content: str) -> None:
        self.messages.append({
            "role": "assistant",
            "content": content,
        })
        self._trim()

    def add_system_message(self, content: str) -> None:
        self.messages.append({
            "role": "system",
            "content": content,
        })
        self._trim()

    # ------------------------------------------------------------------
    # Consulta
    # ------------------------------------------------------------------

    def get_messages(self) -> List[Dict[str, str]]:
        return self.messages.copy()

    def format_for_prompt(self) -> str:
        """
        Formata o histórico para inclusão no prompt.
        """
        if not self.messages:
            return ""

        lines = []

        for message in self.messages:
            role = message["role"].upper()
            content = message["content"]
            lines.append(f"{role}: {content}")

        return "\n".join(lines)

    def clear(self) -> None:
        self.messages.clear()

    def is_empty(self) -> bool:
        return len(self.messages) == 0

    # ------------------------------------------------------------------
    # Controle interno
    # ------------------------------------------------------------------

    def _trim(self) -> None:
        """
        Mantém somente as mensagens mais recentes.
        """
        if len(self.messages) > self.max_history:
            excess = len(self.messages) - self.max_history
            self.messages = self.messages[excess:]


    # ------------------------------------------------------------------
    # Histórico
    # ------------------------------------------------------------------

    def save(self, file_path: str | Path) -> None:
        """
        Salva o histórico em disco.
        """
        path = Path(file_path)

        path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        with path.open(
            "w",
            encoding="utf-8",
        ) as f:
            json.dump(
                self.messages,
                f,
                ensure_ascii=False,
                indent=2,
            )


    def load(self, file_path: str | Path) -> None:
        """
        Carrega histórico salvo.
        """
        path = Path(file_path)

        if not path.exists():
            return

        with path.open(
            "r",
            encoding="utf-8",
        ) as f:
            self.messages = json.load(f)

        self._trim()


    # ------------------------------------------------------------------
    # Representação
    # ------------------------------------------------------------------

    def __len__(self) -> int:
        return len(self.messages)

    def __repr__(self) -> str:
        return (
            f"SessionManager("
            f"messages={len(self.messages)}, "
            f"max_history={self.max_history})"
        )