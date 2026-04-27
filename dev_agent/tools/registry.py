from __future__ import annotations

from typing import Dict

from dev_agent.tools.base import Tool


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: Dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        self._tools[tool.name] = tool

    def unregister(self, name: str) -> None:
        self._tools.pop(name, None)

    def get(self, name: str) -> Tool | None:
        return self._tools.get(name)

    def exists(self, name: str) -> bool:
        return name in self._tools

    def list(self) -> Dict[str, str]:
        return {
            name: tool.description
            for name, tool in self._tools.items()
        }

    def execute(self, name: str, *args, **kwargs):
        tool = self.get(name)

        if tool is None:
            raise ValueError(
                f"Ferramenta '{name}' não registrada."
            )

        return tool.execute(*args, **kwargs)

    def __len__(self) -> int:
        return len(self._tools)