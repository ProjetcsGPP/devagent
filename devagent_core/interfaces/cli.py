from devagent_core.interfaces.chat_session import ChatSession


class DevAgentCLI:
    def __init__(self, bootstrap):
        self.bootstrap = bootstrap
        self.chat_session = ChatSession(bootstrap)

        self.commands = {
            "help": self.cmd_help,
            "status": self.cmd_status,
            "memory": self.cmd_memory,
            "ask": self.cmd_ask,
            "index": self.cmd_index,
            "chat": self.cmd_chat,
            "analyze": self.cmd_analyze,
            "exit": self.cmd_exit,
            "quit": self.cmd_exit,
        }

    def start(self):
        print("\nDigite 'help' para ajuda ou 'exit' para sair.\n")

        while True:
            try:
                command = input("devagent> ").strip()
            except (KeyboardInterrupt, EOFError):
                print("\nEncerrando DevAgent...")
                break

            if not command:
                continue

            self.handle_command(command)

    def handle_command(self, command: str):
        parts = command.split(maxsplit=1)

        action = parts[0].lower()
        argument = parts[1] if len(parts) > 1 else ""

        handler = self.commands.get(action)

        if handler:
            handler(argument)
        else:
            print(f"Comando desconhecido: {action}")

    def cmd_help(self, _):
        print("""
Comandos disponíveis:
  help                Exibe esta ajuda
  status              Mostra status do sistema
  memory              Lista memórias
  ask <pergunta>       Consulta o RAG
  index <arquivo>      Indexa arquivo ou diretório
  chat                 Inicia chat contínuo
  analyze <arquivo>    Analisa um arquivo
  exit                 Encerra o programa
""")

    def cmd_status(self, _):
        print("\n=== STATUS ===")
        print("Memory: active")
        print(f"Index count: {self.bootstrap.index.count()}")
        print("RAG: active")
        print()

    def cmd_memory(self, _):
        rows = self.bootstrap.storage.fetchall(
            "SELECT key, value FROM memory_store ORDER BY key"
        )

        if not rows:
            print("Nenhuma memória armazenada.")
            return

        print("\n=== MEMORY ===")
        for key, value in rows:
            print(f"{key}: {value}")
        print()

    def cmd_ask(self, question):
        if not question:
            print("Uso: ask <pergunta>")
            return

        result = self.bootstrap.rag.query(question)

        print("\n=== RESPOSTA ===")
        print(result["answer"])
        print()

    def cmd_index(self, target):
        if not target:
            print("Uso: index <arquivo|diretório>")
            return

        import os

        try:
            if os.path.isdir(target):
                total = self.bootstrap.index.index_directory(target)
                print(f"{total} arquivos indexados.")
            else:
                self.bootstrap.index.index_file(target)
                print(f"Arquivo indexado: {target}")

        except Exception as e:
            print(f"Erro ao indexar: {e}")

    def cmd_chat(self, _):
        self.chat_session.start()

    def cmd_analyze(self, argument):
        if not argument:
            print("Uso: analyze <arquivo>")
            return

        print("\nAnalisando...\n")
        result = self.bootstrap.analyze_tool.execute(argument)
        print(result)
        print()

    def cmd_exit(self, _):
        print("Encerrando DevAgent...")
        raise SystemExit