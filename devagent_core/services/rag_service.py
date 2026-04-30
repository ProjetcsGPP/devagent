from typing import List, Dict, Any


class RAGService:
    def __init__(self, index_service, llm_service, storage, query_service):
        self.index = index_service
        self.llm = llm_service
        self.storage = storage
        self.query = query_service

    # =====================================================
    # ENTRY POINT
    # =====================================================
    def run(self, question: str) -> Dict[str, Any]:

        matches = self.index.search(question, limit=10) or []

        if not matches:
            return {
                "query": question,
                "results": [],
                "answer": "Nenhum contexto relevante encontrado.",
                "status": "no_context"
            }

        scored_contexts = []

        for item in matches:
            path = item[0] if isinstance(item, tuple) else item

            content = self._get_file_content(path)

            if not content:
                continue

            text_score = self._simple_text_score(question, content)
            tag_score = self._tag_score(path, question)

            final_score = (text_score * 0.5) + (tag_score * 0.5)

            scored_contexts.append({
                "path": path,
                "content": content[:2500],
                "score": final_score
            })

        scored_contexts.sort(key=lambda x: x["score"], reverse=True)

        top_contexts = scored_contexts[:5]

        context_text = self._build_context(top_contexts)
        prompt = self._build_prompt(question, context_text)

        answer = self.llm.generate(prompt)

        return {
            "query": question,
            "results": top_contexts,
            "answer": answer,
            "status": "ok"
        }

    # =====================================================
    # TAG SCORE (CLEAN - QueryService ONLY)
    # =====================================================
    def _tag_score(self, file_path: str, question: str) -> float:

        tags = self.query.get_file_tags_by_file(file_path)

        if not tags:
            return 0.0

        q = question.lower()
        score = 0.0

        for tag in tags:
            # agora FileTag model (não tuple)
            if tag.tag.lower() in q:
                score += tag.weight * tag.confidence

        return min(score, 1.0)

    # =====================================================
    def _simple_text_score(self, question: str, content: str) -> float:
        q_words = set(question.lower().split())
        c_words = set(content.lower().split())

        if not q_words:
            return 0.0

        return len(q_words.intersection(c_words)) / len(q_words)

    # =====================================================
    def _get_file_content(self, path: str) -> str:
        row = self.storage.fetchone(
            "SELECT content FROM files_index WHERE path = ?",
            (path,),
        )
        return row[0] if row else ""

    # =====================================================
    def _build_context(self, contexts: List[Dict[str, Any]]) -> str:
        return "\n\n".join(
            f"### FILE: {c['path']}\n{c['content']}"
            for c in contexts
        )

    def _build_prompt(self, question: str, context: str) -> str:
        return f"""
Você é o DevAgent, um agente de engenharia de software.

Responda com base EXCLUSIVA no contexto abaixo.

================ CONTEXTO ================

{context}

================ PERGUNTA ================

{question}

=========================================

Resposta técnica, objetiva e precisa:
"""

    def chat(self, message: str, history: list) -> str:
        result = self.run(message)
        return result["answer"]