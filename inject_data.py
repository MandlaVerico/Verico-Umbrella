import json
import os

SCRIPT_DIR = os.path.dirname(__file__)

with open(os.path.join(SCRIPT_DIR, "umbrella_report_aggregated.json")) as f:
    data = json.load(f)

with open(os.path.join(SCRIPT_DIR, "dashboard_template.html"), encoding="utf-8") as f:
    html = f.read()

# Only replace the placeholder once, inside the JSON script tag
json_str = json.dumps(data)
# Escape closing script tags defensively
json_str = json_str.replace("</script>", "<\\/script>")

html = html.replace("__DATA_JSON__", json_str)

with open(os.path.join(SCRIPT_DIR, "umbrella_dashboard.html"), "w", encoding="utf-8") as f:
    f.write(html)

print("Injected data into dashboard HTML")
