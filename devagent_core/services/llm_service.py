import requests


class LLMService:
    def __init__(
        self,
        model="qwen2.5-coder:latest",
        base_url="http://localhost:11434",
        max_tokens=900,
    ):
        self.model = model
        self.base_url = base_url
        self.max_tokens = max_tokens

    def generate(self, prompt: str) -> str:
        response = requests.post(
            f"{self.base_url}/api/generate",
            json={
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.1,
                    "num_predict": self.max_tokens,
                    "num_ctx": 4096,
                    "top_p": 0.9,
                    "repeat_penalty": 1.05,
                },
            },
            timeout=180,
        )

        if response.status_code == 404:
            raise RuntimeError(
                f"Modelo '{self.model}' não encontrado. "
                "Execute 'ollama list' para verificar."
            )

        response.raise_for_status()

        data = response.json()
        return data.get("response", "").strip()