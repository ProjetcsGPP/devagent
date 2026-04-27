from rag.vector_store import retrieve
from llama_index.llms.ollama import Ollama

llm = Ollama(
    model="qwen2.5-coder",
    request_timeout=300.0,
    temperature=0.1,
    num_ctx=8192,
)


def run_query(pergunta: str) -> str:
    """
    Query com roteamento inteligente por intenção.
    """

    pergunta_lower = pergunta.lower()

    # ==================================================
    # LOGIN ROUTING
    # ==================================================
    login_terms = [
        "login",
        "autenticar",
        "autenticação",
        "entrar",
        "signin",
        "sessão",
    ]

    if any(term in pergunta_lower for term in login_terms):
        pergunta = (
            pergunta
            + "\n\nPriorize exclusivamente o endpoint "
            "/api/accounts/login/ e ignore endpoints "
            "como /me, /logout ou outros relacionados."
        )

    # ==================================================
    # RETRIEVAL
    # ==================================================
    results = retrieve(pergunta, top_k=5)

    context = "\n\n---\n\n".join(
    item["text"] if isinstance(item, dict) else str(item)
    for item in results
    )

    prompt = f"""
Você é um especialista na API GPP.

Responda usando SOMENTE o contexto abaixo.

Se a pergunta envolver login, autenticação ou acesso,
o endpoint prioritário é sempre:

POST /api/accounts/login/

Nunca escolha /api/accounts/me/ para perguntas de login.

CONTEXTO:
{context}

PERGUNTA:
{pergunta}

RESPOSTA:
"""

    response = llm.complete(prompt)
    return str(response)

# =========================
# CLI
# =========================

def main() -> None:
    print("RAG pronto (FAISS + Ollama)")

    while True:
        try:
            question = input("\n>> ").strip()

            if question.lower() in {"sair", "exit", "quit"}:
                break

            if not question:
                continue

            answer = run_query(question)
            print(f"\n{answer}")

        except KeyboardInterrupt:
            break
        except EOFError:
            break

    print("\nAté logo!")


if __name__ == "__main__":
    main()