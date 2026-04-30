class MILKernel:
    def __init__(self, storage, file_tags, memory_service, query_service=None):

        self.storage = storage
        self.file_tags = file_tags
        self.memory = memory_service
        self.query = query_service

    # =====================================================
    # CONTEXT ENGINE
    # =====================================================
    def build_context(self, query, execution_history):

        rag_results = self._rag(query)

        tag_scores = self._tag_rank(query)

        exec_scores = self._execution_bias(execution_history)

        return self._merge_and_rank(
            rag_results,
            tag_scores,
            exec_scores
        )

    # =====================================================
    # TAG SCORING (CORRIGIDO)
    # =====================================================
    def _tag_rank(self, query):

        tags = self._extract_query_tags(query)

        scores = {}

        for tag in tags:

            files = self.query.search_file_tags(tag) if self.query else []

            for f in files:

                path = f[0]
                weight = f[2]
                confidence = f[3]

                score = weight * confidence

                scores[path] = scores.get(path, 0) + score

        return scores

    # =====================================================
    # EXECUTION BIAS
    # =====================================================
    def _execution_bias(self, history):

        scores = {}

        for h in history[-50:]:

            if not h.get("success"):
                continue

            for file in h.get("files", []):

                scores[file] = scores.get(file, 0) + 1.5

        return scores

    # =====================================================
    # RAG
    # =====================================================
    def _rag(self, query):
        return self.storage.search(query)

    # =====================================================
    # MERGE ENGINE
    # =====================================================
    def _merge_and_rank(self, rag, tags, execs):

        ranking = {}

        for path, content in rag:
            ranking[path] = {
                "content": content,
                "score": 1.0
            }

        for path, score in tags.items():
            if path not in ranking:
                ranking[path] = {
                    "content": self._load(path),
                    "score": 0.5
                }

            ranking[path]["score"] += score

        for path, score in execs.items():
            if path not in ranking:
                continue

            ranking[path]["score"] += score

        return sorted(
            ranking.items(),
            key=lambda x: x[1]["score"],
            reverse=True
        )

    # =====================================================
    # LOAD
    # =====================================================
    def _load(self, path):
        row = self.storage.fetchone(
            "SELECT content FROM files_index WHERE path = ?",
            (path,)
        )
        return row[0] if row else ""