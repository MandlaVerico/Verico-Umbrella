from pypdf import PdfReader
import os

path = os.path.join(os.path.dirname(__file__), "umbrella_report.pdf")
r = PdfReader(path)
print("Pages:", len(r.pages))
for i, p in enumerate(r.pages):
    print(f"--- page {i+1} ---")
    print(p.extract_text()[:1500])
print("File size KB:", round(os.path.getsize(path)/1024, 1))
