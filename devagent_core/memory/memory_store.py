
class MemoryStore:
    def __init__(self):
        self.events = []

    def record(self, event: dict):
        self.events.append(event)

    def all(self):
        return self.events