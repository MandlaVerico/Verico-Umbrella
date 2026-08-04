import json
import os
import re
from collections import defaultdict


def norm_name(s):
    s = s.strip().lower().replace("_", " ")
    return re.sub(r"\s+", " ", s)

SCRIPT_DIR = os.path.dirname(__file__)

with open(os.path.join(SCRIPT_DIR, "umbrella_report_data.json")) as f:
    raw = json.load(f)

# Daily rollup from hourly data
daily = defaultdict(lambda: {"requests": 0, "allowed": 0, "blocked": 0})
for row in raw["requests_by_hour"]:
    d = row["date"]
    c = row["counts"]
    daily[d]["requests"] += c.get("requests", 0)
    daily[d]["allowed"] += c.get("allowedrequests", 0)
    daily[d]["blocked"] += c.get("blockedrequests", 0)

daily_sorted = sorted(daily.items())
daily_series = [
    {"date": d, "requests": v["requests"], "allowed": v["allowed"], "blocked": v["blocked"]}
    for d, v in daily_sorted
]

# Top categories by request count (dedupe, keep top 10, exclude the generic "Application" bucket noise if needed)
top_categories = []
for row in raw["top_categories"][:10]:
    top_categories.append({
        "label": row["category"]["label"],
        "count": row["count"],
        "bandwidth": row.get("bandwidth"),
    })

# Category blocked/allowed breakdown (from summaries_by_category), matched to top categories by label, top 8
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

# Top destinations (overall) and top blocked destinations
def simplify_dest(row):
    cats = row.get("categories") or []
    return {
        "domain": row["domain"],
        "count": row["count"],
        "categories": [c["label"] for c in cats[:2]],
    }

top_destinations = [simplify_dest(r) for r in raw["top_destinations"][:15]]
top_destinations_blocked = [simplify_dest(r) for r in raw["top_destinations_blocked"][:15]]

# Event types (security signal)
event_types = [r for r in raw["top_eventtypes"] if r["count"] > 0]

# Per-site allowed/blocked activity (from top-identities), matched to networks by normalized name
identity_by_name = {}
for row in raw["top_identities"]:
    counts = row.get("counts", {})
    identity_by_name[norm_name(row["identity"]["label"])] = {
        "allowed": counts.get("allowedrequests", 0),
        "blocked": counts.get("blockedrequests", 0),
    }

# Full site/network roster
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

out = {
    "generated_note": "UniFi Umbrella report data (last 30 days)",
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

out_path = os.path.join(SCRIPT_DIR, "umbrella_report_aggregated.json")
with open(out_path, "w") as f:
    json.dump(out, f, indent=2)

print("Wrote", out_path)
print("Daily points:", len(daily_series))
print("Date range:", daily_series[0]["date"], "to", daily_series[-1]["date"])
print("Sites:", len(sites))
print(json.dumps(out["summary"], indent=2))
