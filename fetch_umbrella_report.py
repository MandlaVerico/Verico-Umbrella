import json
import os
import requests

SCRIPT_DIR = os.path.dirname(__file__)


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


def get_token(key, secret):
    resp = requests.post(
        "https://api.umbrella.com/auth/v2/token",
        auth=(key, secret),
        data={"grant_type": "client_credentials"},
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


def get(headers, path, **params):
    params.setdefault("from", "-30days")
    params.setdefault("to", "now")
    params.setdefault("offset", 0)
    r = requests.get(f"https://api.umbrella.com/reports/v2/{path}", headers=headers, params=params)
    r.raise_for_status()
    return r.json()["data"]


def get_networks(headers):
    r = requests.get("https://api.umbrella.com/deployments/v2/networks", headers=headers, params={"limit": 500})
    r.raise_for_status()
    return r.json()


def main():
    env = load_env(os.path.join(SCRIPT_DIR, ".env"))
    token = get_token(env["UMBRELLA_API_KEY"], env["UMBRELLA_API_SECRET"])
    headers = {"Authorization": f"Bearer {token}"}

    report = {}
    report["summary"] = get(headers, "summary", limit=1)
    report["requests_by_hour"] = get(headers, "requests-by-hour", limit=1000)
    report["top_categories"] = get(headers, "top-categories", limit=15)
    report["summaries_by_category"] = get(headers, "summaries-by-category", limit=15)
    report["top_destinations"] = get(headers, "top-destinations", limit=15)
    report["top_destinations_blocked"] = get(headers, "top-destinations", limit=15, verdict="blocked")
    report["top_eventtypes"] = get(headers, "top-eventtypes", limit=10)
    report["top_identities"] = get(headers, "top-identities", limit=200)
    report["networks"] = get_networks(headers)

    out_path = os.path.join(SCRIPT_DIR, "umbrella_report_data.json")
    with open(out_path, "w") as f:
        json.dump(report, f, indent=2)

    print("Saved", out_path)
    print("Summary:", json.dumps(report["summary"], indent=2))
    print("Requests-by-hour count:", len(report["requests_by_hour"]))
    print("Top categories count:", len(report["top_categories"]))
    print("Top destinations count:", len(report["top_destinations"]))
    print("Top destinations blocked count:", len(report["top_destinations_blocked"]))
    print("Networks count:", len(report["networks"]))
    print("Top identities count:", len(report["top_identities"]))


if __name__ == "__main__":
    main()
