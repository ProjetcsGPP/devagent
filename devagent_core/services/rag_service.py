from typing import List, Dict, Any


class RAGService:
    def __init__(self, index_service, llm_service, storage, file_tag_repo=None):
        self.index = index_service
        self.llm = llm_service
        self.storage = storage
        self.file_tag_repo = file_tag_repo

    # -----------------------------
    # QUERY PRINCIPAL (RAG v2)
    # -----------------------------
    def query(self, question: str) -> Dict[str, Any]:
        # 1. busca textual base
        matches = self.index.search(question, limit=10) or []

        # 2. fallback seguro
        if not matches:
            return {
                "query": question,
                "results": [],
                "answer": "Nenhum contexto relevante encontrado.",
                "status": "no_context"
            }

        scored_contexts = []

        # 3. monta contexto com score híbrido
        for item in matches:
            path = item[0] if isinstance(item, tuple) else item

            content = self._get_file_content(path)

            if not content:
                continue

            # score textual base
            text_score = self._simple_text_score(question, content)

            # score semântico via tags
            tag_score = self._tag_score(path, question)

            # score final híbrido
            final_score = (
                (text_score * 0.5) +
                (tag_score * 0.5)
            )

            scored_contexts.append({
                "path": path,
                "content": content[:2500],
                "score": final_score
            })

        # 4. ordena por relevância
        scored_contexts.sort(key=lambda x: x["score"], reverse=True)

        # 5. pega top contextos
        top_contexts = scored_contexts[:5]

        context_text = self._build_context(top_contexts)

        # 6. prompt final
        prompt = self._build_prompt(question, context_text)

        answer = self.llm.generate(prompt)

        return {
            "query": question,
            "results": top_contexts,
            "answer": answer,
            "status": "ok"
        }

    # -----------------------------
    # TAG SCORE (SEMÂNTICO)
    # -----------------------------
    def _tag_score(self, file_path: str, question: str) -> float:
        if not self.file_tag_repo:
            return 0.0

        tags = self.file_tag_repo.get_by_file(file_path)

        if not tags:
            return 0.0

        q = question.lower()

        score = 0.0

        for tag in tags:
            if tag.tag.lower() in q:
                score += tag.weight * tag.confidence

        return min(score, 1.0)

    # -----------------------------
    # TEXTO SCORE (HEURÍSTICO SIMPLES)
    # -----------------------------
    def _simple_text_score(self, question: str, content: str) -> float:
        q_words = set(question.lower().split())
        c_words = set(content.lower().split())

        if not q_words:
            return 0.0

        overlap = len(q_words.intersection(c_words))
        return overlap / len(q_words)

    # -----------------------------
    # FILE CONTENT
    # -----------------------------
    def _get_file_content(self, path: str) -> str:
        row = self.storage.fetchone(
            """
            SELECT content
            FROM files_index
            WHERE path = ?
            """,
            (path,),
        )

        return row[0] if row else ""

    # -----------------------------
    # CONTEXT BUILDER
    # -----------------------------
    def _build_context(self, contexts: List[Dict[str, Any]]) -> str:
        blocks = []

        for c in contexts:
            blocks.append(
                f"### FILE: {c['path']}\n{c['content']}"
            )

        return "\n\n".join(blocks)

    # -----------------------------
    # PROMPT BUILDER
    # -----------------------------
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

    # -----------------------------
    # CHAT (mantido compatível)
    # -----------------------------
    def chat(self, message: str, history: list) -> str:
        result = self.query(message)
        return result["answer"]