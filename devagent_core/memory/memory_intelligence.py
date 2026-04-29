from collections import defaultdict


class MemoryIntelligence:
    """
    Constrói padrões a partir da memória de execução.
    """

    def __init__(self, memory_service):
        self.memory = memory_service

    # =========================================================
    # ANALYZE PATTERNS
    # =========================================================
    def analyze(self):
        patterns = defaultdict(lambda: {
            "count": 0,
            "success": 0,
            "fail": 0,
            "strategies": defaultdict(int),
            "errors": defaultdict(int),
        })

        for e in self.memory.all():

            key = e.get("type", "unknown")
            p = patterns[key]

            p["count"] += 1

            if e.get("success"):
                p["success"] += 1
            else:
                p["fail"] += 1

            strategy = e.get("strategy")
            if strategy:
                p["strategies"][strategy] += 1

            err = e.get("last_error")
            if err:
                p["errors"][err] += 1

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
    
    def most_common_error(self, intent_type: str):

        patterns = self.analyze()
        p = patterns.get(intent_type)

        if not p:
            return None

        # pega apenas eventos de falha
        failures = [
            e for e in self.memory.all()
            if e.get("type") == "execution_failure"
        ]

        errors = defaultdict(int)

        for f in failures:
            err = f.get("last_error") or "unknown"
            errors[err] += 1

        if not errors:
            return None

        return max(errors.items(), key=lambda x: x[1])[0]