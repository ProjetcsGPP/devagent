from devagent_core.interfaces.chat_session import ChatSession


class DevAgentCLI:
    def __init__(self, bootstrap):
        self.bootstrap = bootstrap
        self.chat_session = ChatSession(bootstrap)

    def start(self):
        print("\n🧠 DevAgent pronto (Brain v3 + MIL ativo)\n")
        print("Digite 'exit' para sair.\n")

        while True:
            try:
                user_input = input("devagent> ").strip()
            except (KeyboardInterrupt, EOFError):
                print("\nEncerrando DevAgent...")
                break

            if not user_input:
                continue

            if user_input.lower() in {"exit", "quit"}:
                print("Encerrando DevAgent...")
                break

            self.handle(user_input)

    # =========================================================
    # SINGLE ENTRY POINT
    # =========================================================
    def handle(self, user_input: str):
        try:
            result = self.chat_session.handle(user_input)
            self._render(result)

        except Exception as e:
            print(f"\n❌ Erro no DevAgent: {e}\n")

    # =========================================================
    # OUTPUT ONLY
    # =========================================================
    def _render(self, result: dict):
        success = result.get("success", False)

        if success:
            print("\n✅ EXECUÇÃO CONCLUÍDA")
        else:
            print("\n❌ EXECUÇÃO FALHOU")

        print(f"\nEstratégia: {result.get('strategy', 'unknown')}")
        print(f"Tentativas: {result.get('attempts', 1)}")

        validation = result.get("validation")
        if validation:
            print(f"Erros detectados: {validation.get('errors', 0)}")

        if result.get("output_file"):
            print("\n=== ARQUIVO GERADO ===")
            print(result["output_file"])

        if result.get("generated_code"):
            print("\n=== CÓDIGO ===")
            print(result["generated_code"])

        response = result.get("response")

        if not response:
            response = result.get("generated_code")
        if not response:
            response = result.get("output_file")
        if not response:
            response = result.get("results")

        if response:
            print("\n=== RESPOSTA ===")
            print(response)
        else:
            print("\n=== RESPOSTA ===")
            print("Nenhuma resposta gerada pelo sistema.")

        if result.get("last_error"):
            print("\n=== ÚLTIMO ERRO ===")
            print(result["last_error"])

        print()