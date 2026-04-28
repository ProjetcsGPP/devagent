class MILKernel:
    def __init__(self, storage, file_tags, memory_service):

            self.storage = storage
            self.file_tags = file_tags
            self.memory = memory_service

    # =====================================================
    # CONTEXT ENGINE (FINAL)
    # =====================================================
    def build_context(self, query, execution_history):

        rag_results = self._rag(query)

        tag_scores = self._tag_rank(query)

        exec_scores = self._execution_bias(execution_history)

        merged = self._merge_and_rank(
            rag_results,
            tag_scores,
            exec_scores
        )

        return merged

    # =====================================================
    # TAG SCORING
    # =====================================================
    def _tag_rank(self, query):

        tags = self._extract_query_tags(query)

        scores = {}

        for tag in tags:

            files = self.file_tags.search_by_tag(tag)

            for f in files:

                path = f.file_path

                score = (
                    f.weight *
                    f.confidence
                )

                scores[path] = scores.get(path, 0) + score

        return scores

    # =====================================================
    # EXECUTION BIAS (Brain learning)
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
    # MERGE ENGINE (CORE INTELLIGENCE)
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

    def _load(self, path):
        row = self.storage.fetchone(
            "SELECT content FROM files_index WHERE path = ?",
            (path,)
        )
        return row[0] if row else ""