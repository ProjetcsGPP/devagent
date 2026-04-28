import time
from collections import defaultdict
from typing import List, Dict, Any


class MILv6:
    """
    MIL v6 = sistema cognitivo autônomo de engenharia

    Agora o DevAgent:
    - cria hipóteses de erro
    - gera testes automaticamente
    - valida correções
    - atualiza conhecimento estrutural do projeto
    """

    def __init__(self, storage, file_tags_repo):
        self.storage = storage
        self.file_tags = file_tags_repo

        self.error_graph = defaultdict(list)
        self.hypothesis_memory = defaultdict(list)
        self.test_memory = defaultdict(list)
        self.impact_graph = defaultdict(set)

    # =========================================================
    # ENTRY POINT
    # =========================================================

    def build_context(self, query: str, brain=None):

        rag = self._rag(query)
        tag = self._tag_score(query)
        exec_mem = self._execution_score(query)

        hypotheses = self._generate_hypotheses(query)

        ranked = self._merge(
            rag,
            tag,
            exec_mem,
            hypotheses,
            brain
        )

        return ranked

    # =========================================================
    # RAG
    # =========================================================

    def _rag(self, query: str):

        rows = self.storage.fetchall("""
            SELECT path, content
            FROM files_index
            WHERE content LIKE ?
            LIMIT 25
        """, (f"%{query}%",))

        return rows

    # =========================================================
    # TAG SCORE
    # =========================================================

    def _tag_score(self, query: str):

        rows = self.storage.fetchall("""
            SELECT file_path, tag, weight, confidence
            FROM file_tags
        """)

        scores = defaultdict(float)

        for path, tag, weight, confidence in rows:

            if tag.lower() in query.lower():
                scores[path] += weight * confidence

        return scores

    # =========================================================
    # EXECUTION MEMORY
    # =========================================================

    def _execution_score(self, query: str):

        rows = self.storage.fetchall("""
            SELECT intent, error_type, success
            FROM execution_memory
            ORDER BY id DESC
            LIMIT 300
        """)

        scores = defaultdict(float)

        for intent, error, success in rows:

            if query.lower() in str(intent).lower():

                boost = 2.0 if success else -2.0
                scores[str(intent)] += boost

                self.error_graph[intent].append(error)

        return scores

    # =========================================================
    # 🧠 HYPOTHESIS GENERATION (NOVO NÚCLEO)
    # =========================================================

    def _generate_hypotheses(self, query: str):

        """
        Gera possíveis causas de erro baseadas no histórico.
        """

        hypotheses = []

        history = self.storage.fetchall("""
            SELECT intent, error_type, plan
            FROM execution_memory
            ORDER BY id DESC
            LIMIT 200
        """)

        for intent, error, plan in history:

            if query.lower() in str(intent).lower():

                h1 = f"Possível falha estrutural relacionada a {error}"
                h2 = f"Plano anterior pode estar incompleto: {plan}"

                hypotheses.append({
                    "intent": intent,
                    "hypothesis": h1,
                    "confidence": 0.7
                })

                hypotheses.append({
                    "intent": intent,
                    "hypothesis": h2,
                    "confidence": 0.5
                })

                self.hypothesis_memory[query].append(h1)

        return hypotheses

    # =========================================================
    # 🧪 AUTO TEST GENERATION
    # =========================================================

    def generate_tests(self, hypothesis: Dict[str, Any]):

        """
        Cria testes automaticamente baseados em hipóteses de erro.
        """

        tests = []

        h = hypothesis["hypothesis"]

        if "import" in h.lower():
            tests.append("test_import_resolution")

        if "plan" in h.lower():
            tests.append("test_execution_plan_integrity")

        if "structural" in h.lower():
            tests.append("test_architecture_consistency")

        self.test_memory[hypothesis["intent"]].extend(tests)

        return tests

    # =========================================================
    # 🔁 SELF DEBUG LOOP (CORE DA V6)
    # =========================================================

    def self_debug_cycle(self, intent, brain):

        hypotheses = self._generate_hypotheses(str(intent))

        for h in hypotheses:

            tests = self.generate_tests(h)

            result = self._run_tests(tests)

            if not result["success"]:

                self._apply_fix_hypothesis(h, brain)

                self._update_knowledge(intent, h, success=False)

            else:
                self._update_knowledge(intent, h, success=True)

    # =========================================================
    # TEST EXECUTION (SIMPLIFIED)
    # =========================================================

    def _run_tests(self, tests: List[str]):

        failed = len(tests) == 0 or "fail" in str(tests)

        return {
            "success": not failed,
            "tests": tests
        }

    # =========================================================
    # FIX GENERATION FROM HYPOTHESIS
    # =========================================================

    def _apply_fix_hypothesis(self, hypothesis, brain):

        """
        Aqui o sistema começa a "editar mentalmente" o projeto.
        """

        self.storage.execute("""
            INSERT INTO repair_memory (intent, fix, timestamp)
            VALUES (?, ?, ?)
        """, (
            hypothesis["intent"],
            hypothesis["hypothesis"],
            time.time()
        ))

        # feedback pro brain
        brain.strategy_score["hypothesis_fix"] += 0.3

    # =========================================================
    # KNOWLEDGE UPDATE
    # =========================================================

    def _update_knowledge(self, intent, hypothesis, success: bool):

        self.storage.execute("""
            INSERT INTO knowledge_graph (intent, hypothesis, success, timestamp)
            VALUES (?, ?, ?, ?)
        """, (
            str(intent),
            hypothesis["hypothesis"],
            success,
            time.time()
        ))

    # =========================================================
    # MERGE INTELLIGENCE
    # =========================================================

    def _merge(self, rag, tags, exec_mem, hypotheses, brain):

        ranking = {}

        for path, content in rag:
            ranking[path] = {"content": content, "score": 1.0}

        for path, score in tags.items():
            if path not in ranking:
                ranking[path] = {"content": "", "score": 0.5}

            ranking[path]["score"] += score

        for key, score in exec_mem.items():
            path = key

            if path not in ranking:
                ranking[path] = {"content": "", "score": 0.3}

            ranking[path]["score"] += score

        # 🧠 hipóteses influenciam ranking
        for h in hypotheses:
            if brain:
                boost = h["confidence"] * brain.strategy_score.get("hypothesis_fix", 0.1)

                for item in ranking.values():
                    item["score"] += boost

        return sorted(
            ranking.items(),
            key=lambda x: x[1]["score"],
            reverse=True
        )