# agent/executor.py

import requests

class APIExecutor:
    def __init__(self, base_url):
        self.base_url = base_url
        self.session = requests.Session()

    def post(self, path, payload, cookies=None):
        url = self.base_url + path

        r = self.session.post(
            url,
            json=payload,
            cookies=cookies
        )

        return {
            "status": r.status_code,
            "data": r.json() if r.content else {}
        }