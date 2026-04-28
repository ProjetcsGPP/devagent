from collections import defaultdict


class MemoryIntelligence:
    """
    Constrói padrões a partir da memória de execução.
    """

    def __init__(self, memory_store):
        self.memory = memory_store

    # =========================================================
    # ANALYZE PATTERNS
    # =========================================================
    def analyze(self):

        patterns = defaultdict(lambda: {
            "count": 0,
            "success": 0,
            "fail": 0,
            "strategies": defaultdict(int),
        })

        for e in self.memory.all():

            key = e.get("error_type", "unknown")

            p = patterns[key]

            p["count"] += 1

            if e.get("success"):
                p["success"] += 1
            else:
                p["fail"] += 1

            strategy = e.get("strategy")
            if strategy:
                p["strategies"][strategy] += 1

        return patterns

    # =========================================================
    # BEST STRATEGY FOR ERROR TYPE
    # =========================================================
    def best_strategy(self, error_type: str):

        patterns = self.analyze()

        p = patterns.get(error_type)

        if not p:
            return None

        strategies = p["strategies"]

        if not strategies:
            return None

        return max(strategies.items(), key=lambda x: x[1])[0]