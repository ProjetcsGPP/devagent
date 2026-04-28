from dataclasses import dataclass
from typing import Dict, Any

class DevAgentBrain:
    """
    Orquestrador central do DevAgent.
    Controla ciclo cognitivo completo.
    """

    def __init__(self, bootstrap):
        self.bootstrap = bootstrap

    # =========================================================
    # ENTRY POINT
    # =========================================================
    def handle(self, user_input: str) -> Dict[str, Any]:
        """
        Pipeline principal do agente.
        """

        intent = self._parse_intent(user_input)

        context = self._build_context(intent)

        plan = self._plan(intent, context)

        result = self._execute(plan)

        validation = self._validate(result)

        self._learn(intent, result, validation)

        return {
            "intent": intent,
            "plan": plan,
            "result": result,
            "validation": validation,
        }

    # =========================================================
    # 1. INTENT PARSER
    # =========================================================
    def _parse_intent(self, user_input: str) -> Dict:
        llm = self.bootstrap.llm

        prompt = f"""
Você é um parser de intenção.

Classifique o input abaixo:

- intent: ask | edit | run | test | analyze | fix | chat
- target: arquivo, sistema ou null
- priority: low | medium | high

INPUT:
{user_input}

Responda em JSON.
"""

        try:
            response = llm.generate(prompt)
            return eval(response)  # ideal trocar por json.loads depois
        except Exception:
            return {
                "intent": "ask",
                "target": None,
                "priority": "medium"
            }

    # =========================================================
    # 2. CONTEXT BUILDER (RAG + TAGS)
    # =========================================================
    def _build_context(self, intent: Dict) -> str:
        query = str(intent.get("target") or "")

        rag_context = self.bootstrap.rag.search_context(query)

        tags_context = self._get_tags(intent)

        return f"""
RAG CONTEXT:
{rag_context}

TAGS CONTEXT:
{tags_context}
"""

    def _get_tags(self, intent: Dict) -> str:
        try:
            repo = self.bootstrap.file_tag_repo
            if not repo:
                return "sem tags"

            tags = repo.search_by_intent(intent.get("intent"))

            return "\n".join([str(t) for t in tags])

        except Exception:
            return "erro ao carregar tags"

    # =========================================================
    # 3. PLANNING LAYER
    # =========================================================
    def _plan(self, intent: Dict, context: str) -> Dict:
        llm = self.bootstrap.llm

        prompt = f"""
Você é um planejador de ações de um agente de software.

INTENT:
{intent}

CONTEXTO:
{context}

Gere um plano de execução em lista de passos:

Exemplo:
[
  "analyze file",
  "edit file",
  "run tests"
]
"""

        try:
            response = llm.generate(prompt)
            return eval(response)
        except Exception:
            return ["analyze"]

    # =========================================================
    # 4. EXECUTION LAYER
    # =========================================================
    def _execute(self, plan):
        results = []

        for step in plan:
            if "edit" in step:
                results.append(self.bootstrap.edit_tool.execute(".", "auto fix"))

            elif "run" in step:
                results.append(self.bootstrap.run_tool.execute("."))

            elif "test" in step:
                results.append(self.bootstrap.test_tool.execute("."))

            elif "analyze" in step:
                results.append(self.bootstrap.analyze_tool.execute("."))

        return results

    # =========================================================
    # 5. VALIDATION LAYER
    # =========================================================
    def _validate(self, results):
        errors = [r for r in results if hasattr(r, "success") and not r.success]

        return {
            "success": len(errors) == 0,
            "errors": len(errors),
        }

    # =========================================================
    # 6. LEARNING LAYER
    # =========================================================
    def _learn(self, intent, result, validation):
        try:
            self.bootstrap.memory.store(
                key="last_intent",
                value=str(intent)
            )

            self.bootstrap.memory.store(
                key="last_validation",
                value=str(validation)
            )

        except Exception:
            pass