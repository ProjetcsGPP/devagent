from collections import defaultdict
from typing import Dict
import json
from devagent_core.contracts.event_contract import EventContractV1


class MIL:
    """
    Memory Intelligence Layer (CLEAN FINAL VERSION)

    Regras:
    - Sem SQL direto
    - Tudo via repositories / QueryService
    - Sem lógica duplicada de estratégia
    - Sem mistura Row/dict fora do storage
    """

    def __init__(
        self,
        storage,
        strategy_repository,
        query_service,
        file_tag_service,
    ):
        self.storage = storage
        self.strategy_repository = strategy_repository
        self.query = query_service
        self.file_tag_service = file_tag_service

        self.error_frequency = defaultdict(int)

    # =========================================================
    # STRATEGY SCORING (SAFE)
    # =========================================================
    def _strategy_score(self, strategy: str) -> float:
        data = self.strategy_repository.load_all().get(strategy, {})

        if not data:
            return 0.0

        success = data.get("success_count") or 0
        failure = data.get("failure_count") or 0

        return success - (failure * 0.5)

    def _rank_strategies(self) -> Dict[str, float]:
        all_strategies = self.strategy_repository.load_all()

        scores = {}

        for name in all_strategies:
            scores[name] = self._strategy_score(name)

        return scores

    # =========================================================
    # BEST STRATEGY
    # =========================================================
    def best_strategy(self, intent: str = None) -> str:
        scores = self._rank_strategies()

        return max(scores, key=scores.get) if scores else "default_plan"

    # =========================================================
    # EVENT ENTRY
    # =========================================================
    def process_event(self, event: EventContractV1):
        self.learn_from_event(event)
        self._update_strategy(event)

    # =========================================================
    # STRATEGY UPDATE
    # =========================================================
    def _update_strategy(self, event: EventContractV1):
        strategy = str(event.strategy or "default_plan")

        if event.success:
            self.strategy_repository.register_success(strategy)
        else:
            self.strategy_repository.register_failure(strategy)

            if event.error:
                intent = str(event.intent or "unknown")
                self.error_frequency[(intent, event.error)] += 1

    # =========================================================
    # CONTEXT BUILDER
    # =========================================================
    def build_context(self, query: str, brain=None):
        rag = self._rag(query)
        tag_scores = self._tags(query)
        exec_scores = self._execution(query)
        loop_penalty = self._loop_detection(query)
        brain_scores = self._brain(brain)

        return self._merge(
            rag,
            tag_scores,
            exec_scores,
            loop_penalty,
            brain_scores,
        )

    # =========================================================
    # RAG
    # =========================================================
    def _rag(self, query: str):

        rows = self.query.search_files(query)

        print("\n===== RAG DEBUG =====")
        print("QUERY:", query)
        print("RESULTS:", len(rows))

        for r in rows[:10]:
            print("\nPATH:", r.get("path"))
            print("CONTENT SAMPLE:", (r.get("content") or "")[:200])

        print("=====================\n")

        return rows

    # =========================================================
    # TAGS (SAFE UNPACK)
    # =========================================================
    def _tags(self, query: str):
        scores = defaultdict(float)

        for word in query.lower().split():
            tags = self.query.search_file_tags(word)

            for r in tags:
                file_path = r["file_path"]
                tag = r["tag"]
                weight = r["weight"]
                confidence = r["confidence"]

                scores[file_path] += weight * confidence

        return scores

    # =========================================================
    # EXECUTION MEMORY (SAFE)
    # =========================================================
    def _execution(self, query: str):

        rows = self.query.get_execution_events()
        scores = defaultdict(float)

        for row in rows:

            raw = row.get("data") if isinstance(row, dict) else row[0]

            if not raw:
                continue

            try:
                event = json.loads(raw) if isinstance(raw, str) else raw
            except Exception:
                continue

            intent = str(event.get("intent", ""))

            if query.lower() in intent.lower():
                score = 1.5 if event.get("success") else -2.0
                scores[intent] += score

                error = event.get("error")
                if error:
                    self.error_frequency[(intent, error)] += 1

        return scores

    # =========================================================
    # LOOP DETECTION
    # =========================================================
    def _loop_detection(self, query: str):
        penalty = defaultdict(float)

        for (intent, error), count in self.error_frequency.items():
            if query.lower() in intent.lower() and count >= 3:
                penalty[intent] -= 3.0

        return penalty

    # =========================================================
    # BRAIN
    # =========================================================
    def _brain(self, brain):
        if not brain:
            return {}

        return getattr(brain, "strategy_score", {})

    # =========================================================
    # MERGE ENGINE
    # =========================================================
    def _merge(self, rag, tags, exec_scores, loop_penalty, brain_scores):

        ranking = {}

        for r in rag:
            path = r["path"]
            content = r["content"]

            score = ranking.get(path, {}).get("score", 0.0)

            ranking[path] = {
                "content": content,
                "score": score + 1.0
            }

        for path, score in tags.items():
            if path not in ranking:
                ranking[path] = {"content": "", "score": 0.5}
            ranking[path]["score"] += score

        for intent, score in exec_scores.items():
            path = self._resolve(intent)
            if not path:
                continue

            if path not in ranking:
                ranking[path] = {"content": "", "score": 0.3}

            ranking[path]["score"] += score

        for intent, penalty in loop_penalty.items():
            path = self._resolve(intent)
            if path in ranking:
                ranking[path]["score"] += penalty

        if brain_scores:
            avg = sum(brain_scores.values()) / max(len(brain_scores), 1)
            for item in ranking.values():
                item["score"] += avg * 0.01

        return sorted(
            ranking.items(),
            key=lambda x: x[1]["score"],
            reverse=True,
        )

    # =========================================================
    # LEARNING
    # =========================================================
    def learn_from_event(self, event: EventContractV1):

        files_used = (event.metadata or {}).get("files_used", [])

        for file_path in files_used:

            tags = self.query.get_file_tags_by_file(file_path)

            for row in tags:

                tag = row["tag"]

                delta = 0.2 if event.success else -0.3

                self.file_tag_service.update_weight(
                    file_path,
                    tag,
                    delta,
                )

    # =========================================================
    # RESOLVE
    # =========================================================
    def _resolve(self, key: str):

        results = self.query.find_file_by_tag(key)

        if not results:
            return None

        return results[0]["file_path"] if results else None