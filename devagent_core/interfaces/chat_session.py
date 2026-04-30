from rich.console import Console

console = Console()


class ChatSession:
    def __init__(self, bootstrap):
        self.bootstrap = bootstrap
        self.history = []

    def handle(self, user_input: str):
        result = self.bootstrap.brain.handle(user_input)

        self.history.append({
            "role": "user",
            "content": user_input,
        })

        self.history.append({
            "role": "assistant",
            "content": result.get("response", ""),
        })

        return result

    def clear(self):
        self.history.clear()