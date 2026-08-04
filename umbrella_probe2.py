import os
import requests

def load_env(path):
    env = {}
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or "=" not in line:
                continue
            k, v = line.split("=", 1)
            env[k] = v
    return env

env = load_env(os.path.join(os.path.dirname(__file__), ".env"))
KEY = env["UMBRELLA_API_KEY"]
SECRET = env["UMBRELLA_API_SECRET"]

resp = requests.post(
    "https://api.umbrella.com/auth/v2/token",
    auth=(KEY, SECRET),
    data={"grant_type": "client_credentials"},
)
token = resp.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

urls = [
    "https://api.umbrella.com/reports/v2/top-destinations?from=-30days&to=now&limit=5&offset=0",
    "https://api.umbrella.com/reports/v2/top-categories?from=-30days&to=now&limit=5&offset=0",
    "https://api.umbrella.com/reports/v2/top-threats?from=-30days&to=now&limit=5&offset=0",
    "https://api.umbrella.com/reports/v2/summaries-by-category?from=-30days&to=now&limit=5&offset=0",
    "https://api.umbrella.com/reports/v2/requests-by-hour?from=-30days&to=now&limit=5&offset=0",
    "https://api.umbrella.com/reports/v2/organizations/8245196/top-destinations?from=-30days&to=now&limit=5&offset=0",
]
for url in urls:
    r = requests.get(url, headers=headers)
    print("\nGET", url)
    print("STATUS", r.status_code)
    print(r.text[:500])
