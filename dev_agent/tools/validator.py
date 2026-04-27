"""
dev_agent/tools/validator.py

Validação genérica baseada em schema para o DevAgent v6.
"""

from __future__ import annotations

from typing import Any, Dict, List


class ValidationError(Exception):
    """
    Exceção lançada quando a validação falha.
    """

    def __init__(self, errors: List[str]):
        self.errors = errors
        super().__init__("\n".join(errors))


class ToolValidator:
    """
    Validador de argumentos baseado em schema.
    """

    TYPE_MAP = {
        "string": str,
        "integer": int,
        "number": (int, float),
        "boolean": bool,
        "object": dict,
        "array": list,
    }

    def validate(
        self,
        tool,
        args: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Valida os argumentos de uma tool.

        Retorna os args originais se forem válidos.
        """
        schema = getattr(tool, "schema", {}) or {}

        if not schema:
            return args

        errors: List[str] = []

        self._validate_required(schema, args, errors)
        self._validate_properties(schema, args, errors)

        if errors:
            raise ValidationError(errors)

        return args

    def _validate_required(
        self,
        schema: Dict[str, Any],
        args: Dict[str, Any],
        errors: List[str]
    ) -> None:
        for field in schema.get("required", []):
            if field not in args:
                errors.append(
                    f"Missing required field: '{field}'"
                )

    def _validate_properties(
        self,
        schema: Dict[str, Any],
        args: Dict[str, Any],
        errors: List[str]
    ) -> None:
        properties = schema.get("properties", {})

        for field, rules in properties.items():
            if field not in args:
                continue

            value = args[field]

            self._validate_type(
                field,
                value,
                rules,
                errors
            )

            self._validate_enum(
                field,
                value,
                rules,
                errors
            )

    def _validate_type(
        self,
        field: str,
        value: Any,
        rules: Dict[str, Any],
        errors: List[str]
    ) -> None:
        expected = rules.get("type")

        if not expected:
            return

        python_type = self.TYPE_MAP.get(expected)

        if python_type is None:
            return

        if not isinstance(value, python_type):
            errors.append(
                f"Field '{field}' must be of type '{expected}'"
            )

    def _validate_enum(
        self,
        field: str,
        value: Any,
        rules: Dict[str, Any],
        errors: List[str]
    ) -> None:
        allowed = rules.get("enum")

        if not allowed:
            return

        if value not in allowed:
            errors.append(
                f"Invalid {field}: {value}. "
                f"Allowed: {allowed}"
            )