import time
from typing import Any, Dict


class DevAgentKernel:
    """
    Kernel Final do DevAgent

    Coordena:
    - CLI
    - Brain
    - MIL
    - Tools
    - RAG
    - Memory
    """

    def __init__(self, bootstrap, mil, brain):

        self.bootstrap = bootstrap
        self.mil = mil
        self.brain = brain

        self.history = []

    # =========================================================
    # ENTRY POINT (o cérebro do sistema)
    # =========================================================

    def handle(self, user_input: str) -> Dict[str, Any]:

        # 1. INTENT
        intent = self._parse(user_input)

        # 2. CONTEXT (MIL + RAG + Tags + Exec history)
        context = self.mil.build_context(
            str(intent),
            brain=self.brain
        )

        # 3. STRATEGY (Brain)
        strategy = self._strategy(intent, context)

        # 4. PLAN (LLM)
        plan = self._plan(intent, context, strategy)

        # 5. EXECUTION (Tools)
        result = self._execute(plan)

        # 6. VALIDATION
        validation = self._validate(result)

        # 7. LEARNING (MIL)
        self._learn(intent, plan, result, validation)

        # 8. MEMORY STORE
        self._store(intent, strategy, plan, validation)

        return {
            "intent": intent,
            "strategy": strategy,
            "success": validation["success"],
            "result": result
        }

    # =========================================================
    # INTENT PARSING
    # =========================================================

    def _parse(self, user_input: str):

        llm = self.bootstrap.llm

        prompt = f"""
Retorne JSON:

{{
  "intent": "ask|run|fix|test|edit",
  "target": "{user_input}"
}}
"""

        try:
            return llm.generate(prompt)
        except Exception:
            return {"intent": "ask", "target": user_input}

    # =========================================================
    # STRATEGY (Brain decide)
    # =========================================================

    def _strategy(self, intent, context):

        return self.brain.select_strategy({
            "intent": intent,
            "context": context
        })

    # =========================================================
    # PLANNER (LLM)
    # =========================================================

    def _plan(self, intent, context, strategy):

        llm = self.bootstrap.llm

        prompt = f"""
Você é um planejador de execução de código.

ESTRATÉGIA:
{strategy}

INTENT:
{intent}

CONTEXTO:
{context}

Retorne JSON:
{{
  "steps": ["analyze", "test", "fix"]
}}
"""

        try:
            return llm.generate(prompt)
        except Exception:
            return {"steps": ["analyze"]}

    # =========================================================
    # EXECUTION (Tools)
    # =========================================================

    def _execute(self, plan):

        results = []

        for step in plan.get("steps", []):

            if step == "analyze":
                results.append(self.bootstrap.analyze_tool.execute("."))

            elif step == "test":
                results.append(self.bootstrap.test_tool.execute("."))

            elif step == "run":
                results.append(self.bootstrap.run_tool.execute("."))

            elif step == "edit":
                results.append(self.bootstrap.edit_tool.execute(".", "auto"))

            elif step == "fix":
                results.append(self.bootstrap.auto_fix_v2.execute("."))

        return results

    # =========================================================
    # VALIDATION
    # =========================================================

    def _validate(self, results):

        errors = [
            r for r in results
            if hasattr(r, "success") and not r.success
        ]

        return {
            "success": len(errors) == 0,
            "errors": len(errors)
        }

    # =========================================================
    # LEARNING LOOP (MIL FEEDBACK)
    # =========================================================

    def _learn(self, intent, plan, result, validation):

        files_used = self._extract_files(result)

        self.mil.learn(
            intent=intent,
            success=validation["success"],
            files_used=files_used
        )

        self.brain.reinforce(
            strategy=self.brain.last_strategy,
            success=validation["success"]
        )

    # =========================================================
    # MEMORY STORE
    # =========================================================

    def _store(self, intent, strategy, plan, validation):

        self.history.append({
            "time": time.time(),
            "intent": intent,
            "strategy": strategy,
            "plan": plan,
            "success": validation["success"]
        })

    # =========================================================
    # HELPERS
    # =========================================================

    def _extract_files(self, result):
        # pode evoluir depois para AST / diff tracking
        return []