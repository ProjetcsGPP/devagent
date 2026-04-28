# devagent_core/memory/mil_engine.py

from collections import defaultdict


class MemoryIntelligence:
    """
    Constrói padrões reais de execução.
    """

    def __init__(self, memory_store):
        self.memory = memory_store

    # =========================================================
    # BUILD PATTERNS
    # =========================================================
    def analyze(self):

        patterns = defaultdict(lambda: {
            "count": 0,
            "success": 0,
            "fail": 0,
            "strategies": defaultdict(int),
            "error_types": defaultdict(int),
        })

        for e in self.memory.all():

            key = e.get("intent", {}).get("intent", "unknown")

            p = patterns[key]

            p["count"] += 1

            if e.get("success"):
                p["success"] += 1
            else:
                p["fail"] += 1

            strategy = e.get("strategy")
            if strategy:
                p["strategies"][strategy] += 1

            err = e.get("error_type")
            if err:
                p["error_types"][err] += 1

        return patterns

    # =========================================================
    # BEST STRATEGY
    # =========================================================
    def best_strategy(self, intent_type: str):

        patterns = self.analyze()

        p = patterns.get(intent_type)

        if not p:
            return None

        if not p["strategies"]:
            return None

        return max(p["strategies"].items(), key=lambda x: x[1])[0]

    # =========================================================
    # ERROR INSIGHT
    # =========================================================
    def most_common_error(self, intent_type: str):

        patterns = self.analyze()

        p = patterns.get(intent_type)

        if not p:
            return None

        if not p["error_types"]:
            return None

        return max(p["error_types"].items(), key=lambda x: x[1])[0]