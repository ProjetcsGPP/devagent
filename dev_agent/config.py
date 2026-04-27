from pathlib import Path
import os

# Diretório base do projeto
BASE_DIR = Path.home() / "workspace"

# Diretório do agente
AGENT_DIR = BASE_DIR / "dev_agent"

# Diretório do RAG existente
RAG_DIR = BASE_DIR / "rag"

# Diretório de armazenamento
STORAGE_DIR = BASE_DIR / "storage"

# Ollama
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
MODEL_NAME = os.getenv("OLLAMA_MODEL", "qwen2.5-coder")
EMBEDDING_MODEL = os.getenv("OLLAMA_EMBEDDING_MODEL", "nomic-embed-text")

# Comportamento
MAX_HISTORY = int(os.getenv("DEV_AGENT_MAX_HISTORY", "20"))
ENABLE_RAG = os.getenv("DEV_AGENT_ENABLE_RAG", "true").lower() == "true"
DEBUG = os.getenv("DEV_AGENT_DEBUG", "false").lower() == "true"

# Segurança
ALLOWED_SHELL_COMMANDS = {
    "ls",
    "pwd",
    "cat",
    "head",
    "tail",
    "grep",
    "find",
    "git",
    "pytest",
    "python",
    "pip",
    "tree",
}

# Banner
APP_NAME = "DevAgent"
APP_VERSION = "5.0.0"

def ensure_directories() -> None:
    """
    Garante que os diretórios essenciais existam.
    """
    STORAGE_DIR.mkdir(parents=True, exist_ok=True)