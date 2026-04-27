import os
import json
import numpy as np
import faiss
import requests

# ==========================================================
# CONFIG
# ==========================================================

EMBED_MODEL = "nomic-embed-text"
OLLAMA_URL = "http://localhost:11434/api/embeddings"
RERANK_MODEL = "qwen2.5"

RAG_DIR = os.path.dirname(__file__)
STORAGE_DIR = os.path.join(RAG_DIR, "../storage")
DOCS_DIR = os.path.join(RAG_DIR, "swagger_clean")

INDEX_PATH = os.path.join(STORAGE_DIR, "faiss.index")
DOCSTORE_PATH = os.path.join(STORAGE_DIR, "docstore.json")

# ==========================================================
# EMBEDDINGS
# ==========================================================

def get_embedding(text: str) -> np.ndarray:
    response = requests.post(
        OLLAMA_URL,
        json={
            "model": EMBED_MODEL,
            "prompt": text,
        },
        timeout=300,
    )
    response.raise_for_status()

    return np.array(
        response.json()["embedding"],
        dtype=np.float32
    )

# ==========================================================
# DOCUMENTOS
# ==========================================================

def load_documents():
    docs = []

    for filename in os.listdir(DOCS_DIR):
        if not filename.endswith(".txt"):
            continue

        filepath = os.path.join(DOCS_DIR, filename)

        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        docs.append({
            "id": filename,
            "text": content,
        })

    return docs

# ==========================================================
# BUILD INDEX
# ==========================================================

def build_index():
    docs = load_documents()

    if not docs:
        raise RuntimeError("Nenhum documento encontrado.")

    embeddings = []
    docstore = []

    for doc in docs:
        emb = get_embedding(doc["text"])
        embeddings.append(emb)
        docstore.append(doc)

    embeddings = np.vstack(embeddings)

    index = faiss.IndexFlatL2(embeddings.shape[1])
    index.add(embeddings)

    os.makedirs(STORAGE_DIR, exist_ok=True)

    faiss.write_index(index, INDEX_PATH)

    with open(DOCSTORE_PATH, "w", encoding="utf-8") as f:
        json.dump(docstore, f, ensure_ascii=False, indent=2)

    print(f"[OK] Index built with {len(docstore)} documents")

# ==========================================================
# LOAD INDEX
# ==========================================================

def load_index():
    if not os.path.exists(INDEX_PATH):
        raise FileNotFoundError(
            "Índice FAISS não encontrado. Execute: python rag/vector_store.py"
        )

    index = faiss.read_index(INDEX_PATH)

    with open(DOCSTORE_PATH, "r", encoding="utf-8") as f:
        docstore = json.load(f)

    return index, docstore

# ==========================================================
# SEARCH
# ==========================================================

def search(query: str, top_k: int = 10):
    index, docstore = load_index()

    query_vector = get_embedding(query).reshape(1, -1)

    distances, indices = index.search(
        query_vector.astype(np.float32),
        top_k
    )

    results = []

    for idx in indices[0]:
        if 0 <= idx < len(docstore):
            results.append(docstore[idx])

    return results

# ==========================================================
# RERANK
# ==========================================================

def rerank(query: str, docs: list):
    url = "http://localhost:11434/api/generate"

    scored = []

    for doc in docs:
        prompt = f"""
Você é um reranker de documentos.

Pergunta:
{query}

Documento:
{doc["text"]}

Avalie a relevância de 0 a 10.
Responda SOMENTE com um número.
"""

        response = requests.post(
            url,
            json={
                "model": RERANK_MODEL,
                "prompt": prompt,
                "stream": False,
            },
            timeout=300,
        )

        score_text = response.json()["response"].strip()

        try:
            score = float(score_text)
        except ValueError:
            score = 0.0

        scored.append((score, doc))

    scored.sort(
        key=lambda x: x[0],
        reverse=True
    )

    return [doc for _, doc in scored]

# ==========================================================
# RETRIEVE
# ==========================================================

def retrieve(query: str, top_k: int = 5):
    simple_queries = [
        "login",
        "autenticar",
        "logout",
        "senha",
        "usuário",
    ]

    if any(term in query.lower() for term in simple_queries):
        return search(query, top_k=top_k)

    docs = search(query, top_k=max(top_k, 3))
    ranked = rerank(query, docs[:3])
    return ranked[:top_k]
    
# ==========================================================
# CLI TEST
# ==========================================================

if __name__ == "__main__":
    print("Building index...")
    build_index()

    print("\nSearch test:")

    results = retrieve("login de usuário")

    for result in results:
        print("\n---")
        print(result[:500])