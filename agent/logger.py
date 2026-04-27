# agent/logger.py

import json
from datetime import datetime

class AgentLogger:
    def log(self, event):
        event["timestamp"] = str(datetime.now())

        print(json.dumps(event, indent=2, ensure_ascii=False))