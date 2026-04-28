from devagent_core.interfaces.chat_session import ChatSession


class DevAgentCLI:
    def __init__(self, bootstrap):
        self.bootstrap = bootstrap
        self.chat_session = ChatSession(bootstrap)

    def start(self):
        print("\n🧠 DevAgent pronto (Brain v2 ativo)\n")
        print("Digite 'exit' para sair.\n")

        while True:
            try:
                user_input = input("devagent> ").strip()
            except (KeyboardInterrupt, EOFError):
                print("\nEncerrando DevAgent...")
                break

            if not user_input:
                continue

            if user_input.lower() in ["exit", "quit"]:
                break

            self.handle(user_input)

    # =========================================================
    # SINGLE ENTRY POINT
    # =========================================================
    def handle(self, user_input: str):
        try:
            result = self.bootstrap.brain.handle(user_input)

            self._render(result)

        except Exception as e:
            print(f"\n❌ Erro no Brain: {e}\n")

    # =========================================================
    # OUTPUT ONLY
    # =========================================================
    def _render(self, result: dict):

        if result.get("success"):
            print("\n✅ EXECUÇÃO CONCLUÍDA")

        else:
            print("\n❌ FALHA NA EXECUÇÃO")

        print(f"\nTentativas: {result.get('attempts', 1)}")

        if result.get("validation"):
            print(f"Validação: {result['validation']}")

        if result.get("last_error"):
            print("\n=== ERRO FINAL ===")
            print(result["last_error"])

        print()