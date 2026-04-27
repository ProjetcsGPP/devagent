# agent/llm_router.py

class LLMRouter:
    def __init__(self, qwen, llama):
        self.qwen = qwen
        self.llama = llama

    def run(self, prompt):

        try:
            return self.qwen.complete(prompt)
        except:
            try:
                return self.llama.complete(prompt)
            except:
                return self.rule_fallback(prompt)

    def rule_fallback(self, prompt):
        if "login" in prompt.lower():
            return "USE accounts_login_create"
        return "NO_ACTION"