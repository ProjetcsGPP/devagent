# dev_agent_v4.py

from llama_index.llms.ollama import Ollama

from agent.tool_registry import ToolRegistry
from agent.memory import SessionMemory
from agent.executor import APIExecutor
from agent.llm_router import LLMRouter
from agent.logger import AgentLogger

# ======================
# LLMs
# ======================

qwen = Ollama(model="qwen2.5-coder")
llama = Ollama(model="llama3")

router = LLMRouter(qwen, llama)

# ======================
# CORE SYSTEMS
# ======================

tools = ToolRegistry()
memory = SessionMemory()
logger = AgentLogger()

executor = APIExecutor("http://localhost:8000")

# ======================
# TOOL EXAMPLE (LOGIN)
# ======================

def login_tool(payload, session):
    res = executor.post(
        "/api/accounts/login/",
        payload
    )

    if res["status"] == 200:
        session.set_auth("cookie", "SESSION_OK")

    return res

tools.register("accounts_login", login_tool)

# ======================
# AGENT CORE
# ======================

class DevAgentV4:

    def run(self, user_input, session):

        # 1. LLM decide ação
        decision = router.run(user_input)

        logger.log({
            "input": user_input,
            "decision": decision
        })

        # 2. Tool execution
        if "accounts_login" in decision:
            payload = {
                "username": "joao",
                "password": "123",
                "app_context": "PORTAL"
            }

            result = tools.run("accounts_login", payload, session)

            session.add(result)

            return result

        return {"message": "No action taken"}

# ======================
# LOOP
# ======================

agent = DevAgentV4()
session = SessionMemory()

print("DEV AGENT V4 ON")

while True:
    q = input(">> ")

    if q == "exit":
        break

    response = agent.run(q, session)
    print(response)