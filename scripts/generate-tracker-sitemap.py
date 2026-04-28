#!/usr/bin/env python3
"""
generate-tracker-sitemap.py
Generates sitemap.xml for the ransomware tracker — all 19K+ victim pages.
Run as part of the full --all regeneration.
"""

import sqlite3
from pathlib import Path
from datetime import datetime, timezone

DB_PATH  = Path.home() / "data" / "victims.db"
OUT_PATH = Path.home() / "Downloads/binary-response-site" / "binary-response" / "ransomware-tracker" / "sitemap.xml"
BASE_URL = "https://binary-response.com/ransomware-tracker"

TODAY = datetime.now(timezone.utc).strftime("%Y-%m-%d")

def slugify(text):
    import re, unicodedata
    if not text: return "unknown"
    text = unicodedata.normalize("NFKD", str(text)).encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^\w\s-]", "", text.lower())
    text = re.sub(r"[-\s]+", "-", text).strip("-")
    return text[:80] or "unknown"

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
rows = conn.execute(
    "SELECT company_name, discovered_at FROM disclosures WHERE company_name IS NOT NULL AND company_name != ''"
).fetchall()
conn.close()

PAGES = [
    ("/", 1.0, "hourly"),
    ("/group/", 0.8, "daily"),
    ("/country/", 0.8, "daily"),
    ("/sitemap.xml", 0.5, "monthly"),
]

for r in rows:
    slug = slugify(r["company_name"])
    date = r["discovered_at"][:10] if r["discovered_at"] else TODAY
    PAGES.append((f"/victim/{slug}.html", 0.6, "weekly"))

print(f"Writing {len(PAGES)} URLs to {OUT_PATH}")

with open(OUT_PATH, "w") as f:
    f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
    f.write('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n')
    for loc, priority, changefreq in PAGES:
        f.write(f'  <url><loc>{BASE_URL}{loc}</loc><lastmod>{TODAY}</lastmod><priority>{priority}</priority><changefreq>{changefreq}</changefreq></url>\n')
    f.write('</urlset>\n')

print("Done")
