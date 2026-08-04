import re
import os

SCRIPT_DIR = os.path.dirname(__file__)

with open(os.path.join(SCRIPT_DIR, "umbrella_dashboard.html"), encoding="utf-8") as f:
    html = f.read()

# Replace the embedded JSON data blob back with a placeholder to reconstitute a clean template
pattern = re.compile(
    r'(<script id="report-data" type="application/json">\n)(.*?)(\n</script>)',
    re.DOTALL,
)
new_html, n = pattern.subn(r"\1__DATA_JSON__\3", html)
print("Replacements made:", n)

with open(os.path.join(SCRIPT_DIR, "dashboard_template.html"), "w", encoding="utf-8") as f:
    f.write(new_html)

print("Template length:", len(new_html))
