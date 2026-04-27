# agent/tool_registry.py

class ToolRegistry:
    def __init__(self):
        self.tools = {}

    def register(self, name, func):
        self.tools[name] = func

    def get(self, name):
        return self.tools.get(name)

    def run(self, name, payload, session=None):
        if name not in self.tools:
            raise Exception(f"Tool {name} not found")

        return self.tools[name](payload, session)