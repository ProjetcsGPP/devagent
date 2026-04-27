from llama_index.core import VectorStoreIndex, SimpleDirectoryReader
from llama_index.llms.ollama import Ollama
from llama_index.embeddings.huggingface import HuggingFaceEmbedding

# LLM local
llm = Ollama(model="qwen2.5-coder")

# embeddings
embed_model = HuggingFaceEmbedding( model_name="sentence-transformers/all-MiniLM-L6-v2" )

documents = []

print("Carregando frontend...")

documents += SimpleDirectoryReader(
    "./frontend",
    required_exts=[".ts", ".tsx", ".js", ".json"]
).load_data()

print("Carregando backend...")

documents += SimpleDirectoryReader(
    "./backend", required_exts=[".py"]
).load_data()

print("Carregando swagger limpo...")

documents += SimpleDirectoryReader(
    "rag/swagger_clean"
).load_data()

print(f"Total de documentos: {len(documents)}")

# criar índice

index = VectorStoreIndex.from_documents(
    documents, embed_model=embed_model
)

# salvar

index.storage_context.persist("./storage")

print("Indexação concluída com sucesso!")
