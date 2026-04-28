from typing import Dict, Any, List


class DevAgentBrainV2:
    """
    Brain com loop de auto-correção (self-healing).
    """

    def __init__(self, bootstrap, max_attempts: int = 3):
        self.bootstrap = bootstrap
        self.max_attempts = max_attempts

    # =========================================================
    # ENTRY POINT
    # =========================================================
    def handle(self, user_input: str) -> Dict[str, Any]:

        intent = self._parse_intent(user_input)
        context = self._build_context(intent)

        attempt = 0
        last_result = None
        last_error = None

        while attempt < self.max_attempts:

            plan = self._plan(intent, context, last_error)

            result = self._execute(plan)

            validation = self._validate(result)

            if validation["success"]:
                self._learn(intent, result, validation)
                return {
                    "success": True,
                    "attempts": attempt + 1,
                    "result": result,
                    "validation": validation,
                }

            # ❌ falhou → auto-repair loop
            last_error = self._extract_error(result)

            context = self._enrich_context(context, last_error)

            attempt += 1

        # ❌ falha final
        self._learn(intent, last_result, {"success": False})

        return {
            "success": False,
            "attempts": attempt,
            "last_error": last_error,
        }

    # =========================================================
    # INTENT PARSER
    # =========================================================
    def _parse_intent(self, user_input: str) -> Dict:
        llm = self.bootstrap.llm

        prompt = f"""
Classifique a intenção do usuário:

INPUT:
{user_input}

Responda JSON:
intent, target, priority
"""

        try:
            return eval(llm.generate(prompt))
        except Exception:
            return {
                "intent": "ask",
                "target": None,
                "priority": "medium"
            }

    # =========================================================
    # CONTEXT BUILDER
    # =========================================================
    def _build_context(self, intent: Dict) -> str:
        rag = self.bootstrap.rag.search_context(str(intent.get("target") or ""))

        return f"""
RAG:
{rag}
"""

    def _enrich_context(self, context: str, error: str) -> str:
        return context + f"\n\nERRO DETECTADO:\n{error}"

    # =========================================================
    # PLANNER (com feedback de erro)
    # =========================================================
    def _plan(self, intent: Dict, context: str, error: str = None):

        llm = self.bootstrap.llm

        prompt = f"""
Você é um agente de correção de software.

INTENT:
{intent}

CONTEXTO:
{context}

ERRO ANTERIOR:
{error}

Gere um novo plano de execução.
Responda em lista Python.
"""

        try:
            return eval(llm.generate(prompt))
        except Exception:
            return ["analyze"]

    # =========================================================
    # EXECUTOR
    # =========================================================
    def _execute(self, plan: List[str]):
        results = []

        for step in plan:

            if "edit" in step:
                results.append(
                    self.bootstrap.edit_tool.execute(".", "auto fix")
                )

            elif "run" in step:
                results.append(
                    self.bootstrap.run_tool.execute(".")
                )

            elif "test" in step:
                results.append(
                    self.bootstrap.test_tool.execute(".")
                )

            elif "analyze" in step:
                results.append(
                    self.bootstrap.analyze_tool.execute(".")
                )

            elif "fix" in step:
                results.append(
                    self.bootstrap.auto_fix_v2.execute(".")
                )

        return results

    # =========================================================
    # VALIDATION
    # =========================================================
    def _validate(self, results: List[Any]) -> Dict:

        errors = []

        for r in results:
            if hasattr(r, "success") and not r.success:
                errors.append(r)

        return {
            "success": len(errors) == 0,
            "errors": len(errors)
        }

    # =========================================================
    # ERROR EXTRACTION
    # =========================================================
    def _extract_error(self, results: List[Any]) -> str:
        for r in results:
            if hasattr(r, "stderr") and r.stderr:
                return r.stderr

            if hasattr(r, "error") and r.error:
                return r.error

        return "unknown error"

    # =========================================================
    # MEMORY LEARNING
    # =========================================================
    def _learn(self, intent, result, validation):

        try:
            self.bootstrap.memory.store(
                key="last_intent",
                value=str(intent)
            )

            self.bootstrap.memory.store(
                key="last_result",
                value=str(validation)
            )

        except Exception:
            pass