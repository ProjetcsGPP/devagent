# agent/memory.py

class SessionMemory:
    def __init__(self):
        self.data = {
            "history": [],
            "auth": {},
            "context": None
        }

    def add(self, event):
        self.data["history"].append(event)

    def set_auth(self, key, value):
        self.data["auth"][key] = value

    def get_auth(self):
        return self.data["auth"]