import json
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

SCRIPT_DIR = os.path.dirname(__file__)
env = load_env(os.path.join(SCRIPT_DIR, ".env"))

resp = requests.post(
    "https://api.umbrella.com/auth/v2/token",
    auth=(env["UMBRELLA_API_KEY"], env["UMBRELLA_API_SECRET"]),
    data={"grant_type": "client_credentials"},
)
print("AUTH STATUS", resp.status_code)
print("AUTH BODY", resp.text[:500])
token = resp.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

r = requests.get("https://api.umbrella.com/deployments/v2/networks?limit=500", headers=headers)
print("STATUS", r.status_code)
print("Response headers of interest:")
for k, v in r.headers.items():
    if k.lower() in ("x-total-count", "link", "x-pagination", "total"):
        print(" ", k, "=", v)

data = r.json()
print("Type:", type(data))
print("Count returned:", len(data) if isinstance(data, list) else "n/a")
if isinstance(data, list) and data:
    print("Sample item keys:", list(data[0].keys()))
    statuses = {}
    for item in data:
        statuses[item.get("status")] = statuses.get(item.get("status"), 0) + 1
    print("Status breakdown:", statuses)

with open(os.path.join(SCRIPT_DIR, "networks_full.json"), "w") as f:
    json.dump(data, f, indent=2)
print("Saved full list to networks_full.json")
