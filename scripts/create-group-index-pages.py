#!/usr/bin/env python3
"""
US-004: Generate per-group negotiations index pages.
Creates an index.html inside each of the 24 threat-actor subdirectories,
listing all transcripts in reverse chronological order with dates and links.
"""

import json
import os
import re
import sys
from datetime import datetime

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAPPING_FILE = os.path.join(REPO_ROOT, "negotiations-mapping.json")
NEGOTIATIONS_DIR = os.path.join(REPO_ROOT, "negotiations")

# Display names for each group
GROUP_DISPLAY_NAMES = {
    "akira": "Akira",
    "avaddon": "Avaddon",
    "avos": "AvosLocker",
    "babuk": "Babuk",
    "blackbasta": "Black Basta",
    "blackmatter": "BlackMatter",
    "cloak": "Cloak",
    "conti": "Conti",
    "darkside": "DarkSide",
    "dragonforce": "DragonForce",
    "fog": "Fog",
    "hive": "Hive",
    "hunters-international": "Hunters International",
    "lockbit3-0": "LockBit 3.0",
    "mallox": "Mallox",
    "mount-locker": "Mount Locker",
    "noescape": "NoEscape",
    "pear": "Pear",
    "qilin": "Qilin",
    "ransomhub": "RansomHub",
    "ranzy": "Ranzy Locker",
    "revil": "REvil",
    "runsomewares": "Runsomewares",
    "trinity": "Trinity",
}


def parse_date_from_filename(filename: str, group: str) -> tuple[str, str]:
    """
    Extract a sortable date string and display label from a filename.
    Returns (sort_key, display_label).

    Standard format: {group}-YYYYMMDD[suffix].html → date parsed
    Special cases:
      - dragonforce: GUIDs → use slug as label
      - trinity: 4-digit numbers (trinity-0001.html) → "Case 0001"
      - lockbit3-0: domain names → domain as label
    """
    stem = filename.replace(".html", "")
    # Remove group prefix to get the slug
    prefix = group + "-"
    slug = stem[len(prefix):] if stem.startswith(prefix) else stem

    # Try standard YYYYMMDD date parse (may have suffix like 'b' or '-2' or '-3')
    date_match = re.match(r"^(\d{8})", slug)
    if date_match:
        date_str = date_match.group(1)
        try:
            dt = datetime.strptime(date_str, "%Y%m%d")
            display_date = dt.strftime("%-d %B %Y")
            sort_key = date_str
            return sort_key, display_date
        except ValueError:
            pass

    # Trinity: numeric index like 0001
    if re.match(r"^\d{4}$", slug):
        return slug, f"Case {slug}"

    # DragonForce / lockbit3-0 / others: use slug as label
    return slug, slug


def build_index_html(group: str, files: list[str]) -> str:
    """Generate the index.html content for a group."""
    display_name = GROUP_DISPLAY_NAMES.get(group, group.replace("-", " ").title())
    canonical_url = f"https://binary-response.com/negotiations/{group}/"
    og_title = f"{display_name} Ransomware Negotiation Transcripts"
    page_title = f"{og_title} | Binary Response"

    # Sort files in reverse chronological order
    def sort_key(fname):
        key, _ = parse_date_from_filename(fname, group)
        return key

    sorted_files = sorted(files, key=sort_key, reverse=True)

    # Build transcript list items
    items_html = []
    for fname in sorted_files:
        _, label = parse_date_from_filename(fname, group)
        items_html.append(
            f'      <li class="transcript-item">'
            f'<a href="./{fname}">{display_name} — {label}</a>'
            f"</li>"
        )
    items_str = "\n".join(items_html)
    count = len(files)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>{page_title}</title>
<meta name="description" content="{count} {display_name} ransomware negotiation transcripts. Browse all real-world {display_name} negotiations with full verbatim transcripts.">
<link rel="apple-touch-icon" href="../../img/logo-icon-192.webp">
<link rel="icon" type="image/png" href="../../img/logo-icon.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="preload" as="style" href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=DM+Sans:wght@300;400;600&family=Instrument+Sans:wght@400;600&display=swap" onload="this.onload=null;this.rel='stylesheet'">
<noscript><link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=DM+Sans:wght@300;400;600&family=Instrument+Sans:wght@400;600&display=swap"></noscript>
<link rel="stylesheet" href="../../css/style.css">
<script async src="https://www.googletagmanager.com/gtag/js?id=G-4PMF75NTVG"></script>
<script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments)}}gtag('js',new Date());gtag('config','G-4PMF75NTVG');</script>
<link rel="canonical" href="{canonical_url}">
<meta property="og:title" content="{og_title}">
<meta property="og:description" content="{count} {display_name} ransomware negotiation transcripts. The most complete public archive.">
<meta property="og:url" content="{canonical_url}">
<meta property="og:type" content="website">
<meta property="og:image" content="https://binary-response.com/img/logo-icon.webp">
<meta property="og:site_name" content="Binary Response">
<meta name="twitter:card" content="summary">
<meta name="twitter:image" content="https://binary-response.com/img/logo-icon.webp">
<script type="application/ld+json">
{{
  "@context": "https://schema.org",
  "@graph": [
    {{
      "@type": "CollectionPage",
      "name": "{og_title}",
      "description": "{count} {display_name} ransomware negotiation transcripts.",
      "url": "{canonical_url}",
      "publisher": {{"@type": "Organization", "name": "Binary Response", "url": "https://binary-response.com"}}
    }},
    {{
      "@type": "BreadcrumbList",
      "itemListElement": [
        {{"@type": "ListItem", "position": 1, "name": "Home", "item": "https://binary-response.com/"}},
        {{"@type": "ListItem", "position": 2, "name": "Negotiations", "item": "https://binary-response.com/negotiations/"}},
        {{"@type": "ListItem", "position": 3, "name": "{display_name}", "item": "{canonical_url}"}}
      ]
    }}
  ]
}}
</script>
</head>
<body>
<div class="grid-bg"></div><div class="noise-overlay"></div><div class="scanline"></div>
<nav class="site-nav">
<a href="../../index.html" class="nav-brand">
  <img src="../../img/logo-icon.webp" alt="Binary Response" class="nav-logo" width="32" height="32" fetchpriority="high">
  <span class="nav-name">Binary Response</span>
</a>
<button class="nav-toggle" aria-label="Menu"><span></span><span></span><span></span></button>
<div class="nav-links"></div></nav>

<section class="page-hero" style="position:relative;z-index:2;padding:clamp(6rem,12vw,10rem) 2rem clamp(2rem,4vw,4rem)">
<div style="max-width:900px;margin:0 auto">
<nav aria-label="Breadcrumb" style="margin-bottom:1.5rem;font-size:0.85rem;opacity:0.7">
  <a href="../../index.html">Home</a> &rsaquo;
  <a href="../">Negotiations</a> &rsaquo;
  <span>{display_name}</span>
</nav>
<span class="section-label">// Ransomware Negotiation Transcripts</span>
<h1 style="font-family:var(--display);font-size:clamp(1.8rem,3.5vw,2.8rem);font-weight:700;line-height:1.15;letter-spacing:-0.03em;margin:1rem 0 1.5rem">{display_name} Ransomware <span style="color:var(--accent)">Negotiation Transcripts</span></h1>
<p style="font-size:1.1rem;opacity:0.8;max-width:600px">{count} real-world negotiation transcript{'' if count == 1 else 's'} from {display_name} ransomware operations.</p>
</div>
</section>

<section class="content-section"><div class="container" style="max-width:900px">
<span class="section-label">// All Transcripts</span>
<h2 class="section-title">{display_name} Negotiations</h2>
<ul class="transcript-list" style="list-style:none;padding:0;margin:2rem 0">
{items_str}
</ul>
</div></section>

<footer class="site-footer">
<div class="container">
<p style="opacity:0.6;font-size:0.85rem">&copy; Binary Response Ltd. All rights reserved.</p>
</div>
</footer>
<script src="../../js/nav.js"></script>
<script src="../../js/main.js"></script>
</body>
</html>
"""


def main(dry_run: bool = False) -> int:
    if not os.path.exists(MAPPING_FILE):
        print(f"ERROR: mapping file not found: {MAPPING_FILE}", file=sys.stderr)
        return 1

    with open(MAPPING_FILE) as f:
        mapping: dict[str, list[str]] = json.load(f)

    created = 0
    errors = 0

    for group, files in mapping.items():
        group_dir = os.path.join(NEGOTIATIONS_DIR, group)
        index_path = os.path.join(group_dir, "index.html")

        if not os.path.isdir(group_dir):
            print(f"WARNING: directory does not exist, skipping: {group_dir}", file=sys.stderr)
            errors += 1
            continue

        html = build_index_html(group, files)

        if dry_run:
            print(f"[dry-run] would write {index_path} ({len(files)} transcripts)")
        else:
            with open(index_path, "w", encoding="utf-8") as f:
                f.write(html)
            print(f"Created {index_path} ({len(files)} transcripts)")
            created += 1

    if dry_run:
        print(f"\n[dry-run] would create {len(mapping)} index pages")
    else:
        print(f"\nDone: {created} index pages created, {errors} errors")

    return 0 if errors == 0 else 1


if __name__ == "__main__":
    dry_run = "--dry-run" in sys.argv
    sys.exit(main(dry_run=dry_run))
