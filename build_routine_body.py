import json
import os

SCRIPT_DIR = os.path.dirname(__file__)

with open(os.path.join(SCRIPT_DIR, "dashboard_template.html"), encoding="utf-8") as f:
    TEMPLATE = f.read()

PIPELINE_SCRIPT = '''import json
import re
from collections import defaultdict
import requests

def norm_name(s):
    s = s.strip().lower().replace("_", " ")
    return re.sub(r"\\s+", " ", s)

KEY = "545f344b24234c36b19a1ecc63000bef"
SECRET = "33556b13b899453bb8f0dc9f75f25a47"

def get_token():
    r = requests.post(
        "https://api.umbrella.com/auth/v2/token",
        auth=(KEY, SECRET),
        data={"grant_type": "client_credentials"},
    )
    r.raise_for_status()
    return r.json()["access_token"]

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

def compact(n):
    n = float(n)
    return n

def main():
    token = get_token()
    headers = {"Authorization": f"Bearer {token}"}

    raw = {}
    raw["summary"] = get(headers, "summary", limit=1)
    raw["requests_by_hour"] = get(headers, "requests-by-hour", limit=1000)
    raw["top_categories"] = get(headers, "top-categories", limit=15)
    raw["summaries_by_category"] = get(headers, "summaries-by-category", limit=15)
    raw["top_destinations"] = get(headers, "top-destinations", limit=15)
    raw["top_destinations_blocked"] = get(headers, "top-destinations", limit=15, verdict="blocked")
    raw["top_eventtypes"] = get(headers, "top-eventtypes", limit=10)
    raw["top_identities"] = get(headers, "top-identities", limit=200)
    raw["networks"] = get_networks(headers)

    daily = defaultdict(lambda: {"requests": 0, "allowed": 0, "blocked": 0})
    for row in raw["requests_by_hour"]:
        d = row["date"]
        c = row["counts"]
        daily[d]["requests"] += c.get("requests", 0)
        daily[d]["allowed"] += c.get("allowedrequests", 0)
        daily[d]["blocked"] += c.get("blockedrequests", 0)
    daily_series = [{"date": d, **v} for d, v in sorted(daily.items())]

    top_categories = [
        {"label": r["category"]["label"], "count": r["count"], "bandwidth": r.get("bandwidth")}
        for r in raw["top_categories"][:10]
    ]

    cat_summary = []
    for row in raw["summaries_by_category"]:
        s = row["summary"]
        cat_summary.append({
            "label": row["category"]["label"],
            "requests": s.get("requests", 0),
            "blocked": s.get("requestsblocked", 0),
            "allowed": s.get("requestsallowed", 0),
        })
    cat_summary.sort(key=lambda r: r["blocked"], reverse=True)
    top_blocked_categories = [r for r in cat_summary if r["blocked"] > 0][:10]

    def simplify(row):
        cats = row.get("categories") or []
        return {
            "domain": row["domain"],
            "count": row["count"],
            "categories": [c["label"] for c in cats[:2]],
        }

    top_destinations = [simplify(r) for r in raw["top_destinations"][:15]]
    top_destinations_blocked = [simplify(r) for r in raw["top_destinations_blocked"][:15]]
    event_types = [r for r in raw["top_eventtypes"] if r["count"] > 0]

    identity_by_name = {}
    for row in raw["top_identities"]:
        counts = row.get("counts", {})
        identity_by_name[norm_name(row["identity"]["label"])] = {
            "allowed": counts.get("allowedrequests", 0),
            "blocked": counts.get("blockedrequests", 0),
        }

    sites = []
    for row in raw["networks"]:
        activity = identity_by_name.get(norm_name(row["name"]), {"allowed": 0, "blocked": 0})
        sites.append({
            "name": row["name"],
            "ip_address": row.get("ipAddress"),
            "verified": row.get("isVerified", False),
            "dynamic": row.get("isDynamic", False),
            "created_at": row.get("createdAt", "")[:10],
            "allowed": activity["allowed"],
            "blocked": activity["blocked"],
        })
    sites.sort(key=lambda r: r["name"].lower())

    summary = raw["summary"]
    block_rate = round(100 * summary["requestsblocked"] / summary["requests"], 1) if summary["requests"] else 0

    data = {
        "summary": {
            "total_requests": summary["requests"],
            "allowed_requests": summary["requestsallowed"],
            "blocked_requests": summary["requestsblocked"],
            "block_rate_pct": block_rate,
            "unique_domains": summary["domains"],
            "identities": summary["identities"],
            "categories_seen": summary["categories"],
        },
        "daily_series": daily_series,
        "top_categories": top_categories,
        "top_blocked_categories": top_blocked_categories,
        "top_destinations": top_destinations,
        "top_destinations_blocked": top_destinations_blocked,
        "event_types": event_types,
        "sites": sites,
    }

    with open("dashboard_template.html", encoding="utf-8") as f:
        html = f.read()

    json_str = json.dumps(data).replace("</script>", "<\\\\/script>")
    html = html.replace("__DATA_JSON__", json_str)

    with open("final_dashboard.html", "w", encoding="utf-8") as f:
        f.write(html)

    print("Wrote final_dashboard.html, total_requests=", data["summary"]["total_requests"])

if __name__ == "__main__":
    main()
'''

PROMPT = f"""This is a fully automated recurring hourly job with no human present. Complete every step without asking for confirmation or pausing for input.

GOAL: Refresh a live Cisco Umbrella security/traffic dashboard covering the last 30 days, and republish it via the Artifact tool to the SAME existing artifact URL so the link stays constant while the data refreshes: https://claude.ai/code/artifact/8ead5d4a-e066-49a6-8747-99a2823b79b1

STEP 1: Write a file named dashboard_template.html in your working directory with EXACTLY this content (this is a full HTML fragment, do not alter it):

-----BEGIN dashboard_template.html-----
{TEMPLATE}
-----END dashboard_template.html-----

STEP 2: Write a file named pipeline.py with EXACTLY this content:

-----BEGIN pipeline.py-----
{PIPELINE_SCRIPT}
-----END pipeline.py-----

STEP 3: Ensure the `requests` package is installed (pip install requests if the import fails), then run: python pipeline.py
This authenticates to the Umbrella API, pulls the last 30 days of data, and writes final_dashboard.html in the working directory.

STEP 4: Call the Artifact tool to publish final_dashboard.html with these parameters:
- file_path: the absolute path to final_dashboard.html
- url: https://claude.ai/code/artifact/8ead5d4a-e066-49a6-8747-99a2823b79b1
- favicon: shield emoji
- description: "Last 30 days of Cisco Umbrella data: request volume, blocked vs. allowed traffic, top categories, and top destinations. Refreshed hourly."

If the Umbrella API call fails (auth error, network error, etc.), report the exact error in your final message and stop -- do not retry more than once and do not fabricate data.
"""

body = {
    "job_config": {
        "ccr": {
            "environment_id": "env_017MJbajcWBhQqi9fRLaPDo3",
            "session_context": {
                "model": "claude-sonnet-5",
                "sources": [],
                "allowed_tools": ["Bash", "Read", "Write", "Edit", "Glob", "Grep", "Artifact"],
            },
            "events": [
                {
                    "data": {
                        "uuid": "1a7d35a2-9df6-49b4-8422-c24ad223f742",
                        "session_id": "",
                        "type": "user",
                        "parent_tool_use_id": None,
                        "message": {"role": "user", "content": PROMPT},
                    }
                }
            ],
        }
    }
}

out_path = os.path.join(SCRIPT_DIR, "routine_body.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(body, f)

print("Wrote", out_path, "size bytes:", os.path.getsize(out_path))
