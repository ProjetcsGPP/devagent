from typing import Dict, Any, List
import json
from rich.console import Console

from devagent_core.contracts.event_contract import EventContractV1


class DevAgentBrainV3:

    def __init__(self, bootstrap, mil, max_attempts: int = 3):
        self.bootstrap = bootstrap
        self.mil = mil
        self.max_attempts = max_attempts
        self.console = Console()

    def _extract_target_file(self, text: str):

        import re

        patterns = [
            r"[A-Za-z0-9_]*Service[A-Za-z0-9_]*",
            r"IndexServiceV2_1",
            r"[A-Za-z0-9_]+ServiceV\d+",
        ]

        for p in patterns:
            match = re.search(p, text)
            if match:
                return match.group(0)

        return None


    # =========================================================
    # ENTRY POINT
    # =========================================================
    def handle(self, user_input: str) -> Dict[str, Any]:
        print("\n" + "=" * 80)
        print("🧠 DEVAGENT DEBUG SESSION")
        print("=" * 80)

        self.current_user_input = user_input

        # ------------------------------------------------------------------
        # 1. PARSE INTENT
        # ------------------------------------------------------------------
        print("\n[1] PARSING INTENT")
        print(f"INPUT: {user_input}")

        intent = self._parse_intent(user_input)

        print("INTENT:")
        print(intent)

        # ------------------------------------------------------------------
        # 2. TARGET EXTRACTION
        # ------------------------------------------------------------------
        print("\n[2] EXTRACTING TARGET")

        target = intent.get("target") or user_input
        context_query = self._extract_target_file(target) or target

        print(f"TARGET: {target}")
        print(f"CONTEXT QUERY: {context_query}")

        # ------------------------------------------------------------------
        # 3. RAG / MIL CONTEXT
        # ------------------------------------------------------------------
        print("\n[3] BUILDING CONTEXT")

        raw_context = self.mil.build_context(context_query)

        if isinstance(raw_context, list):
            print(f"RAG RESULTS: {len(raw_context)}")

            for i, item in enumerate(raw_context[:10], start=1):
                if not isinstance(item, dict):
                    continue

                path = item.get("path", "unknown")
                content = str(item.get("content", ""))

                print(f"\n[{i}] PATH: {path}")
                print("-" * 80)
                print(content[:300])
        else:
            print("RAG RETURNED STRING")
            print(str(raw_context)[:1000])

        # ------------------------------------------------------------------
        # 4. PRIMARY CONTEXT
        # ------------------------------------------------------------------
        self.console.print("\n[4] SELECTING PRIMARY CONTEXT")

        primary_context = self._extract_primary_context(
            raw_context,
            context_query,
        )

        if primary_context:
            self.current_primary_context = primary_context or {}

            self.current_context = self.current_primary_context.get(
                "content",
                ""
            )

            # garante defaults críticos
            self.current_primary_context.setdefault("path", "unknown")
            self.current_primary_context.setdefault("score", 0.0)

            self.console.print(
                f"✅ PRIMARY FILE: "
                f"{self.current_primary_context['path']}"
            )

            self.console.print(
                f"⭐ SCORE: "
                f"{float(self.current_primary_context.get('score') or 0):.4f}"
            )

            if context_query.lower() in (
                self.current_primary_context["path"].lower()
            ):
                self.console.print("🎯 MATCH TYPE: exact filename match")
            else:
                self.console.print("📎 MATCH TYPE: semantic similarity")

            self.console.print("-" * 80)
            self.console.print(self.current_context[:2000])

        else:
            self.current_primary_context = None
            self.current_context = ""

            self.console.print(
                "⚠️ PRIMARY CONTEXT: nenhum candidato encontrado."
            )

        # ------------------------------------------------------------------
        # 5. EXECUTION LOOP
        # ------------------------------------------------------------------
        attempt = 0
        last_error = None
        result = None
        strategy = "default_plan"

        while attempt < self.max_attempts:
            self.console.print(
                f"\n[5] EXECUTION ATTEMPT #{attempt + 1}"
            )

            strategy = self.mil_get_strategy(intent)
            self.console.print(f"STRATEGY: {strategy}")

            plan = self._plan(
                intent,
                self.current_context,
                last_error,
                strategy,
            )

            self.console.print(f"PLAN: {plan}")

            # --------------------------------------------------------------
            # 6. PROMPT BUILDING
            # --------------------------------------------------------------
            if hasattr(self, "_build_prompt"):
                prompt = self._build_prompt(
                    intent=intent,
                    plan=plan,
                    context=self.current_context,
                    user_input=self.current_user_input,
                    last_error=last_error,
                )

                self.console.print("\n[6] PROMPT SENT TO LLM")
                self.console.print("-" * 80)
                self.console.print(prompt[:4000])

            # --------------------------------------------------------------
            # 7. EXECUTION
            # --------------------------------------------------------------
            result = self._execute(plan)

            self.console.print("\n[7] EXECUTION RESULT")
            self.console.print("-" * 80)
            self.console.print(result)

            validation = self._validate(result)

            self.console.print("\n[8] VALIDATION")
            self.console.print("-" * 80)
            self.console.print(validation)

            self.mil.process_event(
                EventContractV1.create(
                    type="execution",
                    intent=intent,
                    strategy=strategy,
                    plan=plan,
                    success=validation["success"],
                    error=last_error,
                    metadata={
                        "files_used": self._extract_files(result)
                    },
                )
            )

            if validation["success"]:
                self.console.print("\n✅ EXECUTION SUCCESS")

                self.mil.process_event(
                    EventContractV1.create(
                        type="execution_success",
                        intent=intent,
                        strategy=strategy,
                        plan=plan,
                        success=True,
                    )
                )

                return self._build_response(
                    True,
                    strategy,
                    attempt + 1,
                    validation,
                    result,
                )

            last_error = self._extract_error(result)

            self.console.print("\n❌ EXECUTION FAILED")
            self.console.print(f"ERROR: {last_error}")

            raw_context = self.mil.build_context(context_query)

            primary_context = self._extract_primary_context(
                raw_context,
                context_query,
            )

            if primary_context:
                self.current_primary_context = primary_context
                self.current_context = primary_context.get(
                    "content",
                    "",
                )
            else:
                self.current_primary_context = None
                self.current_context = ""

            attempt += 1

        print("\n🔥 MAX ATTEMPTS REACHED")

        self.mil.process_event(
            EventContractV1.create(
                type="execution_failure",
                intent=intent,
                strategy=strategy,
                success=False,
                error=last_error,
            )
        )

        return self._build_response(
            False,
            strategy,
            attempt,
            {"success": False},
            result,
            last_error,
        )

    # =========================================================
    # ENSURE RESPONSE (FIX CRÍTICO)
    # =========================================================
    def _ensure_response(self, result):

        resp = self._extract_response(result)

        # 🔥 FIX 3 — evita fallback inútil quando RAG falhou
        if resp:
            return resp

        context_text = str(result)

        if not context_text or context_text == "[]":
            return "Não foi possível recuperar contexto do código no RAG."

        return self.bootstrap.llm.generate(f"""
Você é um engenheiro de software.

Explique tecnicamente o resultado abaixo:

INPUT DO USUÁRIO:
{self.current_user_input}

RESULTADO EXECUTADO:
{context_text}

Seja objetivo e técnico.
""")

    # =========================================================
    # RESPONSE BUILDER
    # =========================================================
    def _build_response(self, success, strategy, attempts, validation, result, last_error=None):

        return {
            "success": success,
            "strategy": strategy,
            "attempts": attempts,
            "validation": validation,
            "results": result,
            "response": self._ensure_response(result),
            "generated_code": self._extract_generated_code(result),
            "output_file": self._extract_output_file(result),
            "last_error": last_error,
        }

    # =========================================================
    # STRATEGY SAFE
    # =========================================================
    def mil_get_strategy(self, intent):

        score_table = getattr(self.mil, "strategy_score", None)

        if not score_table:
            return "default_plan"

        try:
            return max(score_table, key=score_table.get)
        except Exception:
            return "default_plan"

    # =========================================================
    # PLANNER
    # =========================================================
    def _plan(self, intent, context, error, strategy):

        llm = self.bootstrap.llm

        prompt = f"""
RETORNE SOMENTE JSON:

{{
  "steps": ["analyze", "test", "fix"]
}}

STRATEGY:
{strategy}

INTENT:
{intent}

CONTEXT:
{context}

ERROR:
{error}
"""

        try:
            data = json.loads(llm.generate(prompt))
            steps = data.get("steps", ["analyze"])
        except Exception:
            steps = ["analyze"]

        # heurística forte
        if intent.get("intent") in {"create", "generate", "code"}:
            return ["analyze", "generate", "run"]

        return steps

    # =========================================================
    # EXECUTION
    # =========================================================

    def _execute(self, plan: List[str]):
        results = []
        generated_file = None

        for step in plan:
            step = step.lower().strip()

            if step == "analyze":
                primary_file = "desconhecido"

                if (
                    hasattr(self, "current_primary_context")
                    and self.current_primary_context
                ):
                    primary_file = self.current_primary_context.get(
                        "path",
                        "desconhecido"
                    )

                self.console.print("\n[5] ANALYSIS CONTEXT")
                self.console.print(f"PRIMARY FILE: {primary_file}")

                prompt = f"""
    Você é um arquiteto de software sênior especialista em engenharia de software.

    Analise EXCLUSIVAMENTE o contexto fornecido abaixo.

    PERGUNTA DO USUÁRIO:
    {self.current_user_input}

    ARQUIVO PRINCIPAL:
    {primary_file}

    CONTEXTO RECUPERADO:
    {self.current_context}

    REGRAS OBRIGATÓRIAS:
    - Responda apenas com base no contexto recuperado.
    - Nunca forneça respostas genéricas.
    - O arquivo principal a ser analisado é: {primary_file}
    - Sempre inicie informando exatamente esse caminho.
    - Ignore arquivos secundários, exceto quando forem dependências diretas.
    - Nunca explique um arquivo diferente do arquivo principal.
    - Se o arquivo principal estiver presente no contexto, priorize-o integralmente.
    - Explique o comportamento real do código apresentado.
    - Descreva fluxo, dependências e papel arquitetural.

    FORMATO DA RESPOSTA:

    Arquivo analisado: {primary_file}

    Responsabilidade:
    ...

    Fluxo de execução:
    1. ...
    2. ...
    3. ...

    Dependências:
    - ...

    Papel na arquitetura:
    ...
    """.strip()

                response = self.bootstrap.llm.generate(prompt)

                self.console.print("\n[6] LLM RESPONSE PREVIEW")
                self.console.print(response[:800])

                results.append({
                    "response": response
                })

            elif step == "generate":
                r = self.bootstrap.code_tool.execute(
                    self.current_user_input
                )
                results.append(r)

                if hasattr(r, "success") and r.success:
                    generated_file = getattr(
                        r,
                        "file_path",
                        None,
                    )

            elif step == "run":
                if generated_file:
                    results.append(
                        self.bootstrap.run_tool.execute(
                            generated_file
                        )
                    )

            elif step == "test":
                if generated_file:
                    results.append(
                        self.bootstrap.run_tool.execute(
                            generated_file
                        )
                    )
                else:
                    results.append(
                        self.bootstrap.test_tool.execute(".")
                    )

            elif step == "fix":
                results.append(
                    self.bootstrap.auto_fix_v2.execute(".")
                )

        return results


    
    # =========================================================
    # VALIDATION
    # =========================================================
    def _validate(self, results):

        errors = [
            r for r in results
            if hasattr(r, "success") and r.success is False
        ]

        return {
            "success": len(errors) == 0,
            "errors": len(errors),
        }

    # =========================================================
    # INTENT
    # =========================================================
    def _parse_intent(self, user_input: str):

        llm = self.bootstrap.llm

        prompt = f"""
    RETORNE SOMENTE JSON VÁLIDO:

    {{
    "intent": "ask",
    "target": "",
    "priority": "normal"
    }}

    INPUT:
    {user_input}
    """

        try:
            raw = llm.generate(prompt)

            start = raw.find("{")
            end = raw.rfind("}") + 1

            if start >= 0 and end > start:
                raw = raw[start:end]

            parsed = json.loads(raw)

            target = parsed.get("target") or user_input.strip()

            return {
                "intent": parsed.get("intent", "ask"),
                "target": target.strip(),
                "priority": parsed.get("priority", "normal")
            }

        except Exception:

            text = user_input.lower()

            if any(w in text for w in [
                "criar",
                "create",
                "generate",
                "codigo",
                "código",
                "implementar",
                "refatorar"
            ]):
                return {
                    "intent": "create",
                    "target": user_input.strip(),
                    "priority": "normal"
                }

            return {
                "intent": "ask",
                "target": user_input.strip(),
                "priority": "normal"
            }

    # =========================================================
    # EXTRACTORS SAFE
    # =========================================================
    def _extract_error(self, results):
        for r in results:
            if hasattr(r, "stderr") and r.stderr:
                return r.stderr
            if hasattr(r, "error") and r.error:
                return r.error
        return None

    def _extract_files(self, results):
        return [
            getattr(r, "file_path", None)
            for r in results
            if getattr(r, "file_path", None)
        ]

    def _extract_response(self, results):
        invalid_markers = [
            "arquivo não encontrado",
            "file not found",
            "not found",
            "nenhum arquivo encontrado",
        ]

        for r in reversed(results):

            candidate = None

            if isinstance(r, dict):
                candidate = (
                    r.get("response")
                    or r.get("stdout")
                )

            else:
                candidate = (
                    getattr(r, "response", None)
                    or getattr(r, "stdout", None)
                )

            if not candidate:
                continue

            text = str(candidate).strip()

            if not text:
                continue

            lower_text = text.lower()

            if any(marker in lower_text for marker in invalid_markers):
                continue

            return text

        return None

    def _extract_generated_code(self, results):
        for r in reversed(results):
            if hasattr(r, "generated_code") and r.generated_code:
                return r.generated_code
            if hasattr(r, "content") and r.content:
                return r.content
        return None

    def _extract_output_file(self, results):
        for r in reversed(results):
            if hasattr(r, "file_path") and r.file_path:
                return r.file_path
        return None


    def _extract_primary_context(self, rag_results, target):
        """
        Seleciona e normaliza o melhor resultado do RAG.

        Aceita formatos:
        - dict
        - tuple(path, content)
        - tuple(path, content, score)
        - list
        """

        if not rag_results:
            return None

        target = (target or "").lower().strip()

        def normalize(item):
            # Já está no formato ideal
            if isinstance(item, dict):
                return {
                    "path": str(item.get("path", "")),
                    "content": str(item.get("content", "")),
                    "score": item.get("score"),
                }

            # Resultado em tuple/list
            if isinstance(item, (tuple, list)):
                path = str(item[0]) if len(item) >= 1 else ""
                content = str(item[1]) if len(item) >= 2 else ""
                score = item[2] if len(item) >= 3 else None

                return {
                    "path": path,
                    "content": content,
                    "score": score,
                }

            # Último fallback
            return {
                "path": "",
                "content": str(item),
                "score": None,
            }

        normalized = [normalize(item) for item in rag_results]

        # 1. Caminho termina exatamente com target
        for item in normalized:
            if item["path"].lower().endswith(target):
                return item

        # 2. Nome do arquivo igual ao target
        for item in normalized:
            filename = item["path"].lower().split("/")[-1]
            if filename == target:
                return item

        # 3. Target aparece no caminho
        for item in normalized:
            if target and target in item["path"].lower():
                return item

        # 4. Primeiro resultado
        return normalized[0]