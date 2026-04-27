"""
dev_agent/main.py

Ponto de entrada do DevAgent.
"""

from __future__ import annotations

import sys

from dev_agent.config import (
    APP_NAME,
    APP_VERSION,
    ensure_directories,
)
from dev_agent.core.agent import DevAgent
from dev_agent.core.llm import OllamaClient, OllamaError


def print_banner() -> None:
    """
    Exibe banner inicial.
    """
    print(
        f"""
{'=' * 60}
{APP_NAME} v{APP_VERSION}
Assistente Local de Desenvolvimento com Ollama + RAG
{'=' * 60}
""".strip()
    )


def check_ollama() -> None:
    """
    Verifica disponibilidade do Ollama.
    """
    client = OllamaClient()

    if not client.is_available():
        print(
            "\n[ERRO] Ollama não está disponível.\n"
            "Inicie o serviço com:\n"
            "    ollama serve\n"
        )
        sys.exit(1)


def interactive_loop(agent: DevAgent) -> None:
    """
    Loop principal do terminal.
    """
    print()
    print(agent.startup_message())
    print()

    try:
        while True:
            user_input = input("dev> ").strip()

            if not user_input:
                continue

            response = agent.process(user_input)

            print()
            print(response)
            print()

    except KeyboardInterrupt:
        print("\n\nEncerrando DevAgent...")

    except EOFError:
        print("\n\nAté logo!")

    except Exception as exc:
        print(f"\n[ERRO] {exc}\n")

    finally:
        try:
            agent.save_session()
            print("Sessão salva com sucesso.")
        except Exception as exc:
            print(
                f"[AVISO] Não foi possível salvar a sessão: {exc}"
            )


def main() -> None:
    """
    Inicialização principal.
    """
    ensure_directories()
    print_banner()
    check_ollama()

    agent = DevAgent()
    interactive_loop(agent)


if __name__ == "__main__":
    main()