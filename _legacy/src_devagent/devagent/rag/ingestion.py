import os
from vector_store import VectorStore

PATH = "rag/swagger_clean"

vs = VectorStore()

for file in os.listdir(PATH):
    if not file.endswith(".txt"):
        continue

    with open(os.path.join(PATH, file), "r", encoding="utf-8") as f:
        text = f.read()

    vs.add(
        text=text,
        meta={"file": file, "text": text}
    )

vs.save()

print("✅ Ingestão concluída")