from collections import defaultdict
from typing import Dict, Any, List
import time
import json


class DevAgentBrainV3:
    """
    Brain adaptativo com aprendizado de estratégia.
    """

    def __init__(self, bootstrap, max_attempts: int = 3):
        self.bootstrap = bootstrap
        self.max_attempts = max_attempts

        self.strategy_score = defaultdict(float)
        self.execution_history = []

        self.memory = bootstrap.memory
        self.memory_ai = bootstrap.memory_intelligence


    def _memory_event(self, event: dict):
        self.memory.record_event(event)


    # =========================================================
    # ENTRY POINT
    # =========================================================
    def handle(self, user_input: str) -> Dict[str, Any]:

        intent = self._parse_intent(user_input)
        context = self._build_context(intent)

        attempt = 0
        last_error = None
        final_validation = {"success": False}

        while attempt < self.max_attempts:

            strategy = self._select_strategy(intent)

            plan = self._plan(intent, context, last_error, strategy)

            result = self._execute(plan)

            validation = self._validate(result)

            self._record_execution(intent, plan, validation, strategy)

            final_validation = validation

            if validation["success"]:
                self._reinforce(strategy, success=True)
                self._learn(intent, result, validation)
                self._learn_from_success(intent, strategy, plan)

                self._memory_event({
                    "type": "execution_success",
                    "intent": intent,
                    "strategy": strategy,
                    "plan": plan,
                    "success": True,
                    "timestamp": time.time()
                })

                return {
                    "success": True,
                    "strategy": strategy,
                    "attempts": attempt + 1,
                    "validation": validation,
                }

            self._reinforce(strategy, success=False)

            last_error = self._extract_error(result)
            context = self._enrich_context(context, last_error)

            attempt += 1

        strategy_final = strategy if 'strategy' in locals() else "unknown"

        self._memory_event({
            "type": "execution_failure",
            "intent": intent,
            "strategy": strategy_final,
            "success": False,
            "last_error": last_error,
            "timestamp": time.time()
        })            
        return {
            "success": False,
            "strategy": strategy_final,
            "attempts": attempt,
            "last_error": last_error,
        }

    
    # =========================================================
    # LEARN FROM SUCCESS
    # =========================================================
    
    def _learn_from_success(self, intent, strategy, plan):

        self._memory_event({
            "type": "success_pattern",
            "intent": intent,
            "strategy": strategy,
            "plan": plan,
            "timestamp": time.time()
        })



    # =========================================================
    # STRATEGY SELECTION
    # =========================================================
    def _select_strategy(self, intent):

        intent_type = intent.get("intent", "ask")

        # 🔥 aprendizado automático
        if self.memory_ai:
            smart = self.memory_ai.best_strategy(intent_type)

            if smart:
                return smart

            # fallback inteligente por erro histórico
            error_hint = self.memory_ai.most_common_error(intent_type)

            if error_hint == "ImportError":
                return "fix_imports"

            if error_hint == "TestFailure":
                return "run_test_fix"

        return "default_plan"

    # =========================================================
    # PLANNER (JSON FIXED)
    # =========================================================
    def _plan(self, intent, context, error, strategy):

        llm = self.bootstrap.llm

        prompt = f"""
Você é um planejador de execução.

RETORNE SOMENTE JSON VÁLIDO:

{{
  "steps": ["analyze", "test", "fix"]
}}

ESTRATÉGIA:
{strategy}

INTENT:
{intent}

CONTEXTO:
{context}

ERRO ANTERIOR:
{error}
"""

        try:
            data = json.loads(llm.generate(prompt))
            return data.get("steps", ["analyze"])
        except Exception:
            return ["analyze"]

    # =========================================================
    # EXECUTION
    # =========================================================
    def _execute(self, plan: List[str]):

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

            elif "fix" in step:
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
            "errors": len(errors),
        }

    # =========================================================
    # LEARNING
    # =========================================================
    def _reinforce(self, strategy: str, success: bool):

        if success:
            self.strategy_score[strategy] += 1.0
        else:
            self.strategy_score[strategy] -= 1.5

    def _learn(self, intent, result, validation):
        # placeholder para MIL futuro
        pass

    # =========================================================
    # MEMORY
    # =========================================================
    def _record_execution(self, intent, plan, validation, strategy):

        self._memory_event({
            "timestamp": time.time(),
            "intent": intent,
            "plan": plan,
            "strategy": strategy,
            "success": validation["success"],
        })

    # =========================================================
    # INTENT PARSER (FIXED JSON)
    # =========================================================
    def _parse_intent(self, user_input: str):

        llm = self.bootstrap.llm

        prompt = f"""
Retorne SOMENTE JSON válido:

{{
  "intent": "ask",
  "target": "",
  "priority": "normal"
}}

INPUT:
{user_input}
"""

        try:
            return json.loads(llm.generate(prompt))
        except Exception:
            return {"intent": "ask", "target": "", "priority": "normal"}

    # =========================================================
    # CONTEXT
    # =========================================================
    def _build_context(self, intent):

        rag = self.bootstrap.rag.search_context(
            str(intent.get("target") or "")
        )

        return f"RAG:\n{rag}"

    def _enrich_context(self, context, error):
        return context + f"\n\nERROR:\n{error}"

    # =========================================================
    # ERROR EXTRACTION
    # =========================================================
    def _extract_error(self, results):

        for r in results:
            if hasattr(r, "stderr") and r.stderr:
                return r.stderr
            if hasattr(r, "error") and r.error:
                return r.error

        return "unknown"


    # =========================================================
    # TAG LEARN
    # =========================================================
    
    def _update_tag_learning(self, result, validation):

        for r in result:

            file_path = getattr(r, "file_path", None)
            if not file_path:
                continue

            tags = self.bootstrap.file_tags.get_by_file(file_path)

            for tag in tags:

                # sucesso reforça
                if validation["success"]:
                    self._increase_tag_weight(tag.tag)

                # erro penaliza
                else:
                    self._decrease_tag_weight(tag.tag)


    def _increase_tag_weight(self, tag_name: str):

        rows = self.bootstrap.storage.fetchall(
            "SELECT file_path, weight FROM file_tags WHERE tag = ?",
            (tag_name,)
        )

        for file_path, weight in rows:

            new_weight = min(weight + 0.2, 5.0)

            self.bootstrap.storage.execute(
                """
                UPDATE file_tags
                SET weight = ?
                WHERE file_path = ? AND tag = ?
                """,
                (new_weight, file_path, tag_name)
            )


    def _decrease_tag_weight(self, tag_name: str):

        rows = self.bootstrap.storage.fetchall(
            "SELECT file_path, weight FROM file_tags WHERE tag = ?",
            (tag_name,)
        )

        for file_path, weight in rows:

            new_weight = max(weight - 0.3, 0.1)

            self.bootstrap.storage.execute(
                """
                UPDATE file_tags
                SET weight = ?
                WHERE file_path = ? AND tag = ?
                """,
                (new_weight, file_path, tag_name)
            )