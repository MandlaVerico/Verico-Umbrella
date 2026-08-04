import base64, json, os, requests

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
resp = requests.post(
    "https://api.umbrella.com/auth/v2/token",
    auth=(env["UMBRELLA_API_KEY"], env["UMBRELLA_API_SECRET"]),
    data={"grant_type": "client_credentials"},
)
token = resp.json()["access_token"]
payload_b64 = token.split(".")[1]
payload_b64 += "=" * (-len(payload_b64) % 4)
payload = json.loads(base64.urlsafe_b64decode(payload_b64))
print(json.dumps(payload, indent=2))
