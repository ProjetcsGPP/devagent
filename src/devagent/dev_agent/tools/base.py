from abc import ABC
from typing import Any, Dict, Optional


class Tool(ABC):
    name: str = "tool"
    description: str = "Ferramenta genérica"

    @property
    def schema(self) -> Dict[str, Any]:
        """
        Schema JSON simplificado da tool.
        Pode ser sobrescrito pelas subclasses.
        """
        return {}

    def execute(
        self,
        args: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Any:
        raise NotImplementedError(
            "Tools devem implementar execute(args, context)"
        )

    def before_execute(self, args: Dict[str, Any], context: Dict[str, Any]) -> None:
        pass

    def after_execute(self, result: Any, context: Dict[str, Any]) -> None:
        pass

    def on_error(self, error: Exception, context: Dict[str, Any]) -> None:
        pass

    def _run(
        self,
        args: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Any:
        context = context or {}

        try:
            self.before_execute(args, context)
            result = self.execute(args, context)
            self.after_execute(result, context)
            return result

        except Exception as e:
            self.on_error(e, context)
            raise

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name='{self.name}')"