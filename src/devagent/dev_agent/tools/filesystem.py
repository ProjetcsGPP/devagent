from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from dev_agent.tools.base import Tool


class FileSystemTool(Tool):
    name = "filesystem"
    description = "Leitura, escrita e listagem de arquivos"

    @property
    def schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "required": ["action"],
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["read", "write", "list"]
                },
                "path": {
                    "type": "string"
                },
                "content": {
                    "type": "string"
                }
            }
        }

    def execute(self, args: Dict[str, Any], context=None):
        context = context or {}

        action = self._safe_str(args.get("action"))

        handlers = {
            "read": self._read_file,
            "write": self._write_file,
            "list": self._list_directory,
        }

        handler = handlers.get(action)

        if handler is None:
            return {
                "error": "invalid action",
                "allowed": ["read", "write", "list"]
            }

        try:
            return handler(args, context)

        except Exception as exc:
            return {
                "error": str(exc),
                "action": action
            }

    def _safe_str(self, value):
        if isinstance(value, str):
            return value.strip()
        return str(value) if value is not None else ""

    def _read_file(self, args, context):
        path = self._safe_str(args.get("path"))
        p = Path(path).expanduser()

        if not p.exists():
            return {"error": f"file not found: {p}"}

        return {
            "path": str(p),
            "content": p.read_text(encoding="utf-8")
        }

    def _write_file(self, args, context):
        path = self._safe_str(args.get("path"))
        content = args.get("content", "")

        p = Path(path).expanduser()
        p.parent.mkdir(parents=True, exist_ok=True)

        p.write_text(str(content), encoding="utf-8")

        return {
            "status": "saved",
            "path": str(p)
        }

    def _list_directory(self, args, context):
        path = self._safe_str(args.get("path", "."))
        p = Path(path).expanduser()

        if not p.exists():
            return {"error": "directory not found"}

        return {
            "items": [str(x.name) for x in sorted(p.iterdir())]
        }