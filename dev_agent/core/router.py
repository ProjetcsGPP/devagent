from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Dict

from dev_agent.tools.validator import ValidationError


@dataclass
class ToolCall:
    tool: str
    args: Dict[str, Any]
    confidence: float = 1.0


class Router:
    def __init__(self, registry, context_builder=None, graph=None, validator=None):
        self.registry = registry
        self.context_builder = context_builder
        self.graph = graph
        self.history = []
        self.validator = validator

    def _build_context(self, tool_call, raw_llm_output):
        base_context = {}

        if self.context_builder:
            base_context = self.context_builder.build(query=raw_llm_output)

        if self.graph and isinstance(tool_call.args, dict):
            path = tool_call.args.get("path")

            if path:
                base_context["impact"] = {
                    "dependencies": self.graph.dependencies_of(path),
                    "dependents": self.graph.dependents_of(path),
                    "impact_analysis": list(
                        self.graph.impact_analysis(path)
                    )
                }

        return base_context

    def parse(self, raw: str) -> ToolCall:
        if not raw or not isinstance(raw, str):
            raise ValueError("LLM output inválido")

        data = json.loads(raw)

        return ToolCall(
            tool=data["tool"],
            args=data.get("args", {}),
            confidence=data.get("confidence", 1.0)
        )

    def execute(self, raw_llm_output: str, context=None):
        context = context or {}

        try:
            tool_call = self.parse(raw_llm_output)

            if tool_call.confidence < 0.3:
                return {
                    "status": "rejected",
                    "reason": "low confidence"
                }

            tool = self.registry.get(tool_call.tool)

            if tool is None:
                return {
                    "status": "error",
                    "error": "tool not found"
                }

            # ✅ Validação antes de construir contexto pesado
            if self.validator:
                tool_call.args = self.validator.validate(
                    tool,
                    tool_call.args
                )

            context.update(
                self._build_context(
                    tool_call,
                    raw_llm_output
                )
            )

            result = tool._run(tool_call.args, context)

            self.history.append({
                "tool": tool_call.tool,
                "args": tool_call.args,
                "context_keys": list(context.keys()),
                "result": str(result)[:500]
            })

            return {
                "status": "success",
                "tool": tool_call.tool,
                "result": result
            }

        except ValidationError as e:
            return {
                "status": "error",
                "error": "validation failed",
                "details": e.errors
            }

        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }