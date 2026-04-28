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
            "edit": self.cmd_edit,
            "exit": self.cmd_exit,
            "run": self.cmd_run,
            "test": self.cmd_test,
            "fix": self.cmd_fix,
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
  help                         Exibe esta ajuda
  status                       Mostra status do sistema
  memory                       Lista memórias
  ask <pergunta>               Consulta o RAG
  index <arquivo|diretório>     Indexa arquivos
  chat                         Inicia chat contínuo
  analyze <arquivo>            Analisa um arquivo
  edit <arquivo> <instrução>   Edita um arquivo usando IA
  exit                         Encerra o programa
  run                          Executa um programa
 test                          Testa um programa
 fix                           corrije um programa
""")

    def cmd_status(self, _):
        print("\n=== STATUS ===")
        print("Memory: active")
        print(f"Index count: {self.bootstrap.index.count()}")
        print("RAG: active")
        print("Edit Tool: active")
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

    def cmd_edit(self, argument):
        """
        Uso:
            edit caminho/do/arquivo.py instrução detalhada

        Exemplo:
            edit devagent_core/core/bootstrap.py adicionar logs de inicialização
        """
        if not argument:
            print("Uso: edit <arquivo> <instrução>")
            return

        # Divide em duas partes:
        # 1. caminho do arquivo
        # 2. instrução para o LLM
        parts = argument.split(maxsplit=1)

        if len(parts) < 2:
            print("Uso: edit <arquivo> <instrução>")
            return

        file_path, instruction = parts

        print(f"\n🛠 Editando: {file_path}")
        print(f"📝 Instrução: {instruction}\n")

        try:
            result = self.bootstrap.edit_tool.execute(
                file_path=file_path,
                instruction=instruction,
            )

            if result.success:
                print("✅ Arquivo editado com sucesso!")

                if result.backup_path:
                    print(f"📦 Backup: {result.backup_path}")

                if result.diff:
                    print("\n=== DIFF RESUMIDO ===")
                    print(result.diff)

                if result.message:
                    print(f"\nℹ️ {result.message}")

            else:
                print(f"❌ Falha: {result.message}")

        except FileNotFoundError:
            print(f"❌ Arquivo não encontrado: {file_path}")

        except PermissionError:
            print(f"❌ Sem permissão para alterar: {file_path}")

        except Exception as e:
            print(f"❌ Erro inesperado: {e}")

    def cmd_run(self, argument):
        """
        Executa um script Python.

        Exemplo:
            run examples/hello.py
        """
        if not argument:
            print("Uso: run <arquivo>")
            return

        print(f"\n▶ Executando: {argument}\n")

        try:
            result = self.bootstrap.run_tool.execute(
                target=argument
            )

            if result.success:
                print("✅ Execução concluída")
            else:
                print("❌ Execução falhou")

            print(f"Comando: {result.command}")
            print(f"Return code: {result.return_code}")

            if result.stdout:
                print("\n=== STDOUT ===")
                print(result.stdout)

            if result.stderr:
                print("\n=== STDERR ===")
                print(result.stderr)

            if result.error:
                print(f"\n❌ Erro: {result.error}")

            print()

        except Exception as e:
            print(f"❌ Erro inesperado: {e}")

    def cmd_test(self, argument):
        """
        Executa testes do projeto.
        Uso:
            test
            test tests/
            test tests/test_api.py
        """
        target = argument.strip() if argument else "."

        print(f"\n🧪 Executando testes: {target}\n")

        try:
            result = self.bootstrap.test_tool.execute(target)

            if result.success:
                print("✅ Testes passaram")
            else:
                print("❌ Testes falharam")

            print(f"Comando: {result.command}")
            print(f"Return code: {result.return_code}")

            if result.stdout:
                print("\n=== STDOUT ===")
                print(result.stdout)

            if result.stderr:
                print("\n=== STDERR ===")
                print(result.stderr)

            if result.error:
                print(f"\n❌ Erro: {result.error}")

            print()

        except Exception as e:
            print(f"❌ Erro inesperado: {e}")

    def cmd_fix(self, argument):
        target = argument.strip() if argument else "."

        print(f"\n🧠 Auto-fix iniciando: {target}\n")

        result = self.bootstrap.auto_fix_v2.execute(target)

        used = "v2"

        if not result.success:
            print("❌ Falha no auto-fix v2. Tentando v1...")
            result = self.bootstrap.auto_fix_tool.execute(target)
            used = "v1"

        if result.success:
            print(f"✅ Auto-fix ({used}) executado com sucesso!")
        else:
            print(f"❌ Auto-fix falhou em ambos (v2 e v1)")

        print(f"Versão usada: {used}")

        if hasattr(result, "attempts"):
            print(f"Tentativas: {result.attempts}")

        if hasattr(result, "summary"):
            print(f"Resumo: {result.summary}")

        if hasattr(result, "last_error") and result.last_error:
            print("\n=== ERRO FINAL ===")
            print(result.last_error)


    def cmd_exit(self, _):
        print("Encerrando DevAgent...")
        raise SystemExit