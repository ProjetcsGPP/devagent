class RAGService:
    def __init__(self, index_service, llm_service, storage):
        self.index = index_service
        self.llm = llm_service
        self.storage = storage

    def build_chat_prompt(
        self,
        message: str,
        context: str,
        history: list,
    ) -> str:
        conversation = ""

        for item in history[-10:]:
            conversation += (
                f"{item['role'].capitalize()}: "
                f"{item['content']}\n"
            )

        return f"""
    Você é DevAgent, um especialista em engenharia de software.

    Contexto do projeto:
    {context}

    Histórico da conversa:
    {conversation}

    Usuário: {message}

    Resposta:
    """

    def query(self, question: str):
        matches = self.index.search(question, limit=5)

        if not matches:
            context = "Nenhum arquivo relevante encontrado."
        else:
            snippets = []

            for path, in matches[:3]:
                row = self.storage.fetchone(
                    """
                    SELECT content
                    FROM files_index
                    WHERE path = ?
                    """,
                    (path,),
                )

                if not row:
                    continue

                content = row[0][:2000]

                snippets.append(
                    f"### Arquivo: {path}\n{content}"
                )

            context = "\n\n".join(snippets)


    def search_context(self, query: str, limit: int = 5) -> str:
        results = self.index.search(query, limit)

        if not results:
            return "Nenhum contexto relevante encontrado."

        contexts = []

        for file_path, *_ in results:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    contexts.append(
                        f"\n### Arquivo: {file_path}\n{content[:4000]}"
                    )
            except Exception:
                continue

        return "\n".join(contexts)

    def chat(self, message: str, history: list) -> str:
        context = self.search_context(message)

        prompt = self.build_chat_prompt(
            message,
            context,
            history,
        )

        return self.llm.generate(prompt)

        prompt = f"""
Você é DevAgent, um arquiteto de software especializado em análise de código.

IMPORTANTE:
- Responda SOMENTE com base no contexto fornecido.
- O contexto pertence ao projeto atual do usuário.
- Se existir uma classe, função ou arquivo com o nome solicitado, explique esse código.
- Nunca responda com definições genéricas.
- Nunca explique tecnologias externas, a menos que estejam explicitamente no contexto.
- Se a informação não estiver no contexto, diga claramente isso.

================ CONTEXTO ================

{context}

================ PERGUNTA ================

{question}

==========================================

Resposta técnica, objetiva, detalhada e em português:
"""

        answer = self.llm.generate(prompt)

        return {
            "query": question,
            "results": matches,
            "answer": answer,
            "status": "ok",
        }