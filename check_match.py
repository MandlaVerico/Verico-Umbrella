import json
import os
import re

SCRIPT_DIR = os.path.dirname(__file__)
with open(os.path.join(SCRIPT_DIR, "umbrella_report_data.json")) as f:
    raw = json.load(f)

def norm(s):
    s = s.strip().lower().replace("_", " ")
    s = re.sub(r"\s+", " ", s)
    return s

identity_names = {norm(r["identity"]["label"]) for r in raw["top_identities"]}
network_names = {norm(r["name"]) for r in raw["networks"]}

matched = network_names & identity_names
unmatched_networks = network_names - identity_names
unmatched_identities = identity_names - network_names

print("Networks:", len(network_names))
print("Identities:", len(identity_names))
print("Matched:", len(matched))
print("Networks with no identity match (likely zero traffic):", len(unmatched_networks))
for n in sorted(unmatched_networks):
    print("  -", n)
print("Identities with no network match (unexpected):", len(unmatched_identities))
for n in sorted(unmatched_identities):
    print("  -", n)
