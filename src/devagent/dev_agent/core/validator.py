"""
dev_agent/core/validator.py

Tool Validation Engine do DevAgent v6.

Responsável por:
- validar schema de tools
- corrigir inputs simples automaticamente
- bloquear execuções inválidas
"""

from __future__ import annotations

from typing import Any, Dict, Tuple


class ValidationError(Exception):
    pass


class ToolValidator:
    """
    Validador central de tools.
    """

    # ------------------------------------------------------------
    # ENTRYPOINT PRINCIPAL
    # ------------------------------------------------------------

    def validate(self, tool, args: Dict[str, Any]) -> Dict[str, Any]:
        """
        Valida args contra schema da tool.
        """

        schema = tool.schema()

        if not schema:
            # tool sem schema → passa direto (compatibilidade v5)
            return args

        validated = {}

        for key, rule in schema.items():

            if key not in args:
                if rule.get("required", False):
                    raise ValidationError(f"Campo obrigatório ausente: {key}")
                continue

            value = args[key]

            validated[key] = self._validate_field(key, value, rule)

        return validated

    # ------------------------------------------------------------
    # VALIDAÇÃO DE CAMPO INDIVIDUAL
    # ------------------------------------------------------------

    def _validate_field(self, key: str, value: Any, rule: Dict[str, Any]) -> Any:

        expected_type = rule.get("type")

        # ---------------------------
        # TYPE CHECK
        # ---------------------------
        if expected_type:
            if expected_type == "str" and not isinstance(value, str):
                raise ValidationError(f"{key} deve ser string")

            if expected_type == "int" and not isinstance(value, int):
                raise ValidationError(f"{key} deve ser int")

            if expected_type == "dict" and not isinstance(value, dict):
                raise ValidationError(f"{key} deve ser dict")

        # ---------------------------
        # ENUM CHECK
        # ---------------------------
        if "enum" in rule:
            if value not in rule["enum"]:
                raise ValidationError(
                    f"{key} inválido. Esperado: {rule['enum']}"
                )

        # ---------------------------
        # STRING RULES
        # ---------------------------
        if isinstance(value, str):

            if rule.get("min_length") and len(value) < rule["min_length"]:
                raise ValidationError(f"{key} muito curto")

            if rule.get("max_length") and len(value) > rule["max_length"]:
                raise ValidationError(f"{key} muito longo")

        return value

    # ------------------------------------------------------------
    # SAFE MODE (FUTURO: AUTO FIX)
    # ------------------------------------------------------------

    def safe_validate(self, tool, args: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
        """
        Tenta validar sem quebrar fluxo.
        Retorna (ok, args_corrigido)
        """

        try:
            return True, self.validate(tool, args)
        except ValidationError:
            return False, {}