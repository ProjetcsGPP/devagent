from dev_agent.tools.registry import ToolRegistry
from dev_agent.tools.filesystem import FileSystemTool
from dev_agent.core.router import Router

registry = ToolRegistry()
registry.register(FileSystemTool())

router = Router(registry)

fake_llm_output = """
{
  "tool": "filesystem",
  "args": {
    "action": "read",
    "path": "test.txt"
  },
  "confidence": 0.9
}
"""

result = router.execute(fake_llm_output)

print(result)