from rich.console import Console

console = Console()


class ChatSession:
    def __init__(self, bootstrap):
        self.bootstrap = bootstrap
        self.history = []

    def start(self):
        console.print("\n[bold green]Modo Chat iniciado[/bold green]")
        console.print("Digite 'exit' para sair.\n")

        while True:
            user_input = input("chat> ").strip()

            if user_input.lower() in {"exit", "quit"}:
                break

            if not user_input:
                continue

            response = self.bootstrap.rag.chat(
                user_input,
                self.history,
            )

            self.history.append({
                "role": "user",
                "content": user_input,
            })

            self.history.append({
                "role": "assistant",
                "content": response,
            })

            console.print(f"\n[cyan]{response}[/cyan]\n")