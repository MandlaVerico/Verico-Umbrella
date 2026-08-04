import os
import requests

def load_env(path):
    env = {}
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
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
print("TOKEN STATUS", resp.status_code)
print(resp.text[:500])

if resp.status_code == 200:
    token = resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    for url in [
        "https://api.umbrella.com/reports/v2/organizations",
        "https://api.umbrella.com/reports/v2/top-destinations?from=-30days&to=now&limit=5",
        "https://api.umbrella.com/admin/v2/organizations",
    ]:
        r = requests.get(url, headers=headers)
        print("\nGET", url)
        print("STATUS", r.status_code)
        print(r.text[:800])
