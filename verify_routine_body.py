import json
import os
import re
import subprocess
import sys
import tempfile
import shutil

SCRIPT_DIR = os.path.dirname(__file__)

with open(os.path.join(SCRIPT_DIR, "routine_body.json"), encoding="utf-8") as f:
    body = json.load(f)

content = body["job_config"]["ccr"]["events"][0]["data"]["message"]["content"]

template = re.search(
    r"-----BEGIN dashboard_template\.html-----\n(.*?)\n-----END dashboard_template\.html-----",
    content, re.DOTALL,
).group(1)

pipeline = re.search(
    r"-----BEGIN pipeline\.py-----\n(.*?)\n-----END pipeline\.py-----",
    content, re.DOTALL,
).group(1)

print("Template length:", len(template))
print("Pipeline length:", len(pipeline))

tmpdir = tempfile.mkdtemp(prefix="umbrella_routine_test_")
try:
    with open(os.path.join(tmpdir, "dashboard_template.html"), "w", encoding="utf-8") as f:
        f.write(template)
    with open(os.path.join(tmpdir, "pipeline.py"), "w", encoding="utf-8") as f:
        f.write(pipeline)

    result = subprocess.run(
        [sys.executable, "pipeline.py"],
        cwd=tmpdir, capture_output=True, text=True, timeout=120,
    )
    print("STDOUT:", result.stdout)
    print("STDERR:", result.stderr[-2000:] if result.stderr else "")
    print("Return code:", result.returncode)

    final_path = os.path.join(tmpdir, "final_dashboard.html")
    if os.path.exists(final_path):
        with open(final_path, encoding="utf-8") as f:
            final_html = f.read()
        print("final_dashboard.html size:", len(final_html))
        print("Contains __DATA_JSON__ placeholder (should be False):", "__DATA_JSON__" in final_html)
        print("Contains 'sites-heading' :", "sites-heading" in final_html)
        m = re.search(r'"sites":\[(.*?)\]', final_html)
        print("Has sites array:", m is not None)
finally:
    shutil.rmtree(tmpdir, ignore_errors=True)
