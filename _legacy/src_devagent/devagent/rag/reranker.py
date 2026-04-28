from sentence_transformers import CrossEncoder

model = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")

def rerank(query, results):
    pairs = [(query, r["text"]) for r in results]

    scores = model.predict(pairs)

    for i, score in enumerate(scores):
        results[i]["rerank_score"] = float(score)

    return sorted(results, key=lambda x: x["rerank_score"], reverse=True)