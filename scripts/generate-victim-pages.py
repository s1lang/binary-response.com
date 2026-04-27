#!/usr/bin/env python3
"""
generate_victim_pages.py
Generates static HTML victim detail pages for the ransomware tracker.
One HTML file per victim at /ransomware-tracker/victim/{slug}.html

Usage:
  python3 generate_victim_pages.py [--limit N] [--since YYYY-MM-DD]
  python3 generate_victim_pages.py --all        (regenerate everything)
  python3 generate_victim_pages.py --recent    (last 7 days only)
"""

import sqlite3
import json
import re
import unicodedata
import argparse
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

DB_PATH    = Path.home() / "data" / "victims.db"
OUT_DIR    = Path.home() / "Downloads/binary-response-site" / "binary-response" / "ransomware-tracker" / "victim"
SITE_URL   = "https://binary-response.com"
TRACKER_URL = f"{SITE_URL}/ransomware-tracker"

# ── Helpers ───────────────────────────────────────────────────────────────────

def slugify(text):
    if not text:
        return "unknown"
    text = unicodedata.normalize("NFKD", str(text))
    text = text.encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^\w\s-]", "", text.lower())
    text = re.sub(r"[-\s]+", "-", text).strip("-")
    return text[:80] or "unknown"


def esc(s):
    """HTML-escape a string."""
    if s is None:
        return ""
    return (str(s)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#39;"))


def region_name(code):
    """Map ISO 3166-1 alpha-2 to full country name."""
    MAP = {
        "US":"United States","GB":"United Kingdom","DE":"Germany","FR":"France",
        "CA":"Canada","IT":"Italy","BR":"Brazil","ES":"Spain","AU":"Australia",
        "JP":"Japan","CH":"Switzerland","MX":"Mexico","IL":"Israel","TH":"Thailand",
        "IN":"India","TW":"Taiwan","AR":"Argentina","CZ":"Czech Republic",
        "KR":"South Korea","TR":"Turkey","CN":"China","SG":"Singapore",
        "AT":"Austria","NL":"Netherlands","ZA":"South Africa","PL":"Poland",
        "CO":"Colombia","PE":"Peru","HK":"Hong Kong","SE":"Sweden","MY":"Malaysia",
        "AE":"United Arab Emirates","ID":"Indonesia","RO":"Romania","EG":"Egypt",
        "BE":"Belgium","PH":"Philippines","RU":"Russia","UA":"Ukraine",
        "NG":"Nigeria","VN":"Vietnam","SA":"Saudi Arabia","NO":"Norway",
        "DK":"Denmark","FI":"Finland","NZ":"New Zealand","IE":"Ireland",
        "PT":"Portugal","GR":"Greece","CL":"Chile","EC":"Ecuador","PE":"Peru",
        "PA":"Panama","PR":"Puerto Rico","CR":"Costa Rica","SK":"Slovakia",
        "HU":"Hungary","RS":"Serbia","BG":"Bulgaria","HR":"Croatia",
        "SI":"Slovenia","LT":"Lithuania","EE":"Estonia","LV":"Latvia",
        "IS":"Iceland","LU":"Luxembourg","MT":"Malta","CY":"Cyprus",
        "GE":"Georgia","AM":"Armenia","AZ":"Azerbaijan","KZ":"Kazakhstan",
        "BD":"Bangladesh","PK":"Pakistan","LK":"Sri Lanka","NP":"Nepal",
        "ID":"Indonesia","MY":"Malaysia","PH":"Philippines","TH":"Thailand",
        "VN":"Vietnam","MM":"Myanmar","KH":"Cambodia","LA":"Laos",
        "NZ":"New Zealand","FJ":"Fiji","PG":"Papua New Guinea",
        "ZA":"South Africa","KE":"Kenya","GH":"Ghana","NG":"Nigeria",
        "EG":"Egypt","MA":"Morocco","DZ":"Algeria","TN":"Tunisia","LB":"Lebanon",
        "JO":"Jordan","IQ":"Iraq","IR":"Iran","SA":"Saudi Arabia","AE":"UAE",
        "QA":"Qatar","KW":"Kuwait","BH":"Bahrain","OM":"Oman","YE":"Yemen",
        "US":"United States","CA":"Canada","MX":"Mexico","GT":"Guatemala",
        "BZ":"Belize","HN":"Honduras","SV":"El Salvador","NI":"Nicaragua",
        "CR":"Costa Rica","PA":"Panama","CO":"Colombia","VE":"Venezuela",
        "EC":"Ecuador","PE":"Peru","BO":"Bolivia","CL":"Chile","AR":"Argentina",
        "PY":"Paraguay","UY":"Uruguay","BR":"Brazil","GY":"Guyana","SR":"Suriname",
    }
    return MAP.get(code, code or "")


# ── Page template ──────────────────────────────────────────────────────────────

def victim_page(row, all_groups, slug=None):
    vid       = row["id"]
    name      = row["company_name"] or "Unknown Organisation"
    domain    = row["domain"] or ""
    sector    = row["sector"] or ""
    region_c  = row["region"] or ""
    region_n  = region_name(region_c)
    actor     = row["threat_actor"] or "Unknown"
    claim_url = row["claim_url"] or ""
    source_url = row["source_url"] or ""
    source    = row["source_site"] or ""
    desc      = row["description"] or ""
    disc_date = row["disclosure_date"] or ""
    disc_dt   = disc_date[:10] if disc_date else ""
    disc_full = disc_date if disc_date else ""
    disc_ts   = None
    if disc_date:
        try:
            # Try parsing as ISO format with Z suffix
            disc_ts = datetime.fromisoformat(disc_date.replace("Z", "+00:00"))
        except Exception:
            try:
                # Try dateutil parser for messy formats
                import dateutil.parser
                disc_ts = dateutil.parser.parse(disc_date)
            except Exception:
                disc_ts = None

    disc_fmt  = disc_ts.strftime("%d %b %Y") if disc_ts else ""
    disc_iso  = disc_ts.strftime("%Y-%m-%d") if disc_ts else ""

    # Make datetime.now() naive so comparison works with naive parsed dates
    now_naive = datetime.utcnow()
    is_new = disc_ts and (now_naive - disc_ts.replace(tzinfo=None)).days <= 7

    slug      = slugify(name) if slug is None else slug
    page_url  = f"{TRACKER_URL}/victim/{slug}.html"
    actor_slug = slugify(actor)
    group_url = f"{TRACKER_URL}/group/{quote(actor_slug)}/index.html"

    data_types = []
    try:
        data_types = json.loads(row["data_types"] or "[]")
    except Exception:
        pass

    vol = row["data_volume_gb"]
    vol_str = f"{vol:,.0f} GB" if vol else ""

    status_map = {
        "new":       ("New",        "status-new"),
        "reviewing": ("Reviewing",  "status-review"),
        "contacted": ("Contacted",  "status-contacted"),
        "engaged":   ("Engaged",    "status-engaged"),
        "closed":    ("Closed",     "status-closed"),
        "declined":  ("Declined",   "status-declined"),
        "suppressed":("Suppressed", "status-suppressed"),
    }
    status_raw = row["status"] or "new"
    status_label, status_cls = status_map.get(status_raw, (status_raw, "status-new"))

    # JSON-LD
    ld = {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": f"{name} — Ransomware Victim",
        "description": desc[:200] if desc else f"{name} was listed as a victim by {actor}.",
        "datePublished": disc_iso,
        "author": {"@type": "Person", "name": "Simon Lynge", "url": f"{SITE_URL}/about.html"},
        "publisher": {"@type": "Organization", "name": "Binary Response", "url": SITE_URL},
        "url": page_url,
    }

    # Precompute meta desc (f-strings can't contain backslash in expression)
    meta_desc = esc((desc[:160] if desc else f"{name} was listed as a ransomware victim by {actor} on their dark web leak site.")[:160])
    og_desc   = esc((desc[:160] if desc else f"{name} ransomware victim listing by {actor}.")[:160])

    # Precompute detail card values
    country_link = (f"<a href='/ransomware-tracker/country/" + esc(region_c) + "/index.html'>" + esc(region_n) + "</a>") if region_n else "Unknown"
    sector_link  = (f"<a href='/ransomware-tracker/?sector=" + quote(sector) + "'>" + esc(sector) + "</a>") if sector else "Not specified"
    domain_link  = (f"<a href='https://" + esc(domain) + "' target='_blank' rel='noopener'>" + esc(domain) + "</a>") if domain else "Not available"
    data_pub_val = "Yes — data posted to leak site" if row["data_published"] else "Not yet published"
    vol_card     = (f"<div class='detail-card'><div class='detail-label'>Data Volume</div><div class='detail-value'>" + esc(vol_str) + "</div></div>") if vol_str else ""
    data_types_card = ("<div class='detail-card'><div class='detail-label'>Data Types</div><div class='detail-value'>" + ", ".join(f"<span class='data-tag'>" + esc(t) + "</span>" for t in data_types[:6]) + "</div></div>") if data_types else ""
    desc_html    = ("<div class='section'><h2>Incident Description</h2><div class='victim-description'>" + "<p>" + "</p><p>".join(esc(d).strip() for d in desc.split("\n") if d.strip()) + "</p></div></div>") if desc else ""

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>{esc(name)} — Ransomware Victim | Binary Response</title>
<meta name="description" content="{meta_desc}">
<link rel="canonical" href="{page_url}">
<meta property="og:title" content="{esc(name)} — Ransomware Victim | Binary Response">
<meta property="og:description" content="{og_desc}">
<meta property="og:url" content="{page_url}">
<meta property="og:type" content="article">
<meta property="og:image" content="{SITE_URL}/img/logo-icon.webp">
<meta property="og:site_name" content="Binary Response">
<meta name="twitter:card" content="summary">
<script type="application/ld+json">{json.dumps(ld, indent=2)}</script>
<link rel="stylesheet" href="/css/style.css">
<style>
.victim-header {{display:flex;align-items:flex-start;gap:1.5rem;margin:1.5rem 0;flex-wrap:wrap}}
.victim-title-block {{flex:1}}
.victim-title-block h1 {{font-size:1.9rem;margin:0.25rem 0 0.5rem;color:var(--text-primary);font-family:var(--display)}}
.victim-meta {{display:flex;gap:0.75rem;flex-wrap:wrap;align-items:center}}
.tag {{display:inline-block;font-size:0.72rem;padding:3px 8px;border-radius:4px;font-family:'JetBrains Mono',monospace}}
.tag-group {{background:rgba(224,85,85,0.12);color:#e05555;border:1px solid rgba(224,85,85,0.25)}}
.tag-new {{background:rgba(0,229,160,0.12);color:#00e5a0;border:1px solid rgba(0,229,160,0.25)}}
.tag-country {{background:rgba(126,179,224,0.1);color:#7eb3e0;border:1px solid rgba(126,179,224,0.2)}}
.victim-badge {{display:inline-flex;align-items:center;gap:0.4rem;font-size:0.75rem;padding:3px 10px;border-radius:20px;font-family:'JetBrains Mono',monospace}}
.badge-new {{background:rgba(0,229,160,0.1);color:#00e5a0;border:1px solid rgba(0,229,160,0.2)}}
.badge-30d {{background:rgba(255,184,77,0.1);color:#ffb84d;border:1px solid rgba(255,184,77,0.2)}}
.detail-grid {{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:0.75rem;margin:1.5rem 0}}
.detail-card {{background:#0f1923;border:1px solid #1e3a5f;border-radius:8px;padding:1rem}}
.detail-label {{font-size:0.7rem;color:#556677;text-transform:uppercase;letter-spacing:1px;margin-bottom:0.3rem}}
.detail-value {{font-size:0.95rem;color:#ccd8e0}}
.detail-value a {{color:#7eb3e0;text-decoration:none}}
.detail-value a:hover {{text-decoration:underline}}
.section {{margin:2rem 0}}
.section h2 {{color:#7eb3e0;font-size:1rem;margin-bottom:1rem;padding-bottom:0.5rem;border-bottom:1px solid rgba(126,179,224,0.15)}}
.data-tags {{display:flex;gap:0.5rem;flex-wrap:wrap}}
.data-tag {{background:rgba(255,184,77,0.08);color:#ffb84d;border:1px solid rgba(255,184,77,0.15);padding:2px 8px;border-radius:4px;font-size:0.75rem;font-family:'JetBrains Mono',monospace}}
.victim-description {{background:#0d1520;border:1px solid #1a2d40;border-radius:8px;padding:1.25rem;color:#8899aa;line-height:1.75;font-size:0.92rem}}
.victim-description p {{margin:0 0 1rem}}
.victim-description p:last-child {{margin-bottom:0}}
.related-group {{background:#0f1923;border:1px solid #1e3a5f;border-radius:8px;padding:1.25rem}}
.related-group a {{color:#e05555;font-family:'JetBrains Mono',monospace;font-size:0.9rem}}
.back-link {{display:inline-flex;align-items:center;gap:0.4rem;color:#7eb3e0;font-size:0.85rem;margin:1.5rem 0;text-decoration:none}}
.back-link:hover {{text-decoration:underline}}
.disclaimer {{background:rgba(255,77,106,0.05);border:1px solid rgba(255,77,106,0.15);border-radius:6px;padding:1rem;margin-top:2rem;font-size:0.82rem;color:#7a8599;line-height:1.6}}
.disclaimer strong {{color:#e05555}}
.action-bar {{background:#0f1923;border:1px solid #1e3a5f;border-radius:8px;padding:1.25rem;margin-top:1.5rem;display:flex;gap:1rem;flex-wrap:wrap;align-items:center}}
.btn {{display:inline-flex;align-items:center;gap:0.4rem;padding:0.6rem 1.2rem;border-radius:6px;font-size:0.85rem;font-weight:600;text-decoration:none;transition:all 0.2s}}
.btn-primary {{background:#00e5a0;color:#080c14}}
.btn-primary:hover {{background:#00c78a}}
.btn-outline {{background:transparent;border:1px solid rgba(126,179,224,0.3);color:#7eb3e0}}
.btn-outline:hover {{background:rgba(126,179,224,0.08)}}
</style>
</head>
<body>
<nav class="site-nav"><a href="/index.html" class="nav-brand"><img src="/img/logo-icon.webp" alt="Binary Response" class="nav-logo" width="32" height="32"><span class="nav-name">Binary Response</span></a><button class="nav-toggle" aria-label="Menu"><span></span><span></span><span></span></button><div class="nav-links"></div></nav>

<div class="tracker-container">
  <nav class="breadcrumbs">
    <a href="/index.html" class="bc-link">Home</a> /
    <a href="/ransomware-tracker/" class="bc-link">Tracker</a> /
    <a href="/ransomware-tracker/?q={quote(name)}" class="bc-link">Victims</a> /
    <span class="bc-current">{esc(name[:40])}</span>
  </nav>

  <div class="victim-header">
    <div class="victim-title-block">
      <h1>{esc(name)}</h1>
      <div class="victim-meta">
        <a href="{group_url}" class="tag tag-group">{esc(actor)}</a>
        {"<span class='victim-badge badge-new'>🆕 New this week</span>" if is_new else ""}
      </div>
    </div>
  </div>

  <div class="detail-grid">
    <div class="detail-card">
      <div class="detail-label">Country</div>
      <div class="detail-value">{"<a href='/ransomware-tracker/country/" + esc(region_c) + "/index.html'>" + esc(region_n) + "</a>" if region_n else "Unknown"}</div>
    </div>
    <div class="detail-card">
      <div class="detail-label">Sector</div>
      <div class="detail-value">{"<a href='/ransomware-tracker/?sector=" + quote(sector) + "'>" + esc(sector) + "</a>" if sector else "Not specified"}</div>
    </div>
    <div class="detail-card">
      <div class="detail-label">Threat Actor</div>
      <div class="detail-value"><a href="{group_url}">{esc(actor)}</a></div>
    </div>
    <div class="detail-card">
      <div class="detail-label">Disclosed</div>
      <div class="detail-value">{esc(disc_fmt)}</div>
    </div>
    <div class="detail-card">
      <div class="detail-label">Domain</div>
      <div class="detail-value">{domain_link}</div>
    </div>
    <div class="detail-card">
      <div class="detail-label">Data Published</div>
      <div class="detail-value">{data_pub_val}</div>
    </div>
    {vol_card}
    {data_types_card}
  </div>

  {desc_html}

  <div class="section">
    <h2>Threat Actor Profile</h2>
    <div class="related-group">
      <p style="color:#8899aa;margin-bottom:0.75rem;font-size:0.9rem">This victim was listed by the following ransomware group:</p>
      <p style="margin-bottom:0.5rem"><a href="{group_url}">→ View all {len(all_groups.get(actor, []))} victims of {esc(actor)}</a></p>
    </div>
  </div>

  <div class="action-bar">
    <a href="/contact.html" class="btn btn-primary">⚡ Report an Incident</a>
    <a href="/ransomware-tracker/" class="btn btn-outline">← Back to Tracker</a>
  </div>

  <div class="disclaimer">
    <strong>⚠️</strong> This entry reflects a claim published by <strong>{esc(actor)}</strong> on their dark web leak site.
    Binary Response does not independently verify all claims. Some records may reflect exaggerated or unconfirmed disclosures.
    Treat this data as <strong>threat intelligence</strong>, not confirmed incident reports.
    For incident response support, <a href="/contact.html" style="color:#7eb3e0">contact Binary Response</a>.
  </div>
</div>

<footer class="site-footer"></footer>
<script src="/js/footer.js"></script>
<script src="/js/nav.js"></script>
</body>
</html>"""
    return html


# ── Main ─────────────────────────────────────────────────────────────────────

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def get_all_groups(conn):
    """Return {group_name: [list of victim slugs]} for cross-linking."""
    rows = conn.execute(
        "SELECT company_name, threat_actor FROM disclosures WHERE company_name IS NOT NULL"
    ).fetchall()
    groups = {}
    for r in rows:
        actor = r["threat_actor"] or "unknown"
        groups.setdefault(actor, []).append(slugify(r["company_name"]))
    return groups


def generate_pages(conn, since=None, limit=None):
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    groups = get_all_groups(conn)

    where = "WHERE company_name IS NOT NULL AND company_name != '' "
    args = []
    if since:
        where += "AND discovered_at >= ? "
        args.append(since)
    where += "ORDER BY discovered_at DESC"
    if limit:
        where += f" LIMIT {limit}"

    rows = conn.execute(
        f"SELECT * FROM disclosures {where}",
        args
    ).fetchall()

    created = 0
    skipped = 0
    seen_slugs = {}  # slug -> count for collision detection
    slug_for_name = {}  # company_name -> resolved slug (for sitemap)

    for row in rows:
        name = row["company_name"]
        if not name:
            skipped += 1
            continue

        base_slug = slugify(name)
        # Resolve slug collisions by appending numeric suffix
        slug = base_slug
        counter = 1
        while slug in seen_slugs:
            slug = f"{base_slug}-{counter}"
            counter += 1
        seen_slugs[slug] = True
        slug_for_name[name] = slug

        out_path = OUT_DIR / f"{slug}.html"
        html = victim_page(row, groups, slug=slug)
        out_path.write_text(html, encoding="utf-8")
        created += 1

    return created, skipped, slug_for_name


def generate_sitemap_index(rows, slug_for_name):
    """Generate /ransomware-tracker/victim/sitemap.xml listing all victim pages."""
    sitemap_path = OUT_DIR / "sitemap.xml"
    urls = []
    for r in rows:
        name = r["company_name"] or "unknown"
        slug = slug_for_name.get(name, slugify(name))
        url = f"{TRACKER_URL}/victim/{slug}.html"
        date = (r["discovered_at"] or "")[:10]
        urls.append(
            f"  <url>\n    <loc>{url}</loc>\n"
            f"    <lastmod>{date}</lastmod>\n"
            f"    <changefreq>monthly</changefreq>\n"
            f"    <priority>0.6</priority>\n"
            f"  </url>"
        )
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{chr(10).join(urls)}
</urlset>"""
    sitemap_path.write_text(xml, encoding="utf-8")
    return sitemap_path


if __name__ == "__main__":
    import sys
    p = argparse.ArgumentParser()
    p.add_argument("--all", action="store_true", help="Regenerate all pages")
    p.add_argument("--recent", action="store_true", help="Last 7 days only")
    p.add_argument("--limit", type=int, help="Limit to N records")
    p.add_argument("--since", help="Only victims discovered since YYYY-MM-DD")
    args = p.parse_args()

    conn = get_db()

    since = args.since
    if args.recent:
        from datetime import timedelta
        since = (datetime.now(timezone.utc) - timedelta(days=7)).strftime("%Y-%m-%d")

    if args.all:
        limit = None
        since = None
    else:
        limit = args.limit or 500

    print(f"Generating pages to {OUT_DIR} ...")
    created, skipped, slug_for_name = generate_pages(conn, since=since, limit=limit)
    print(f"  Created: {created}  Skipped: {skipped}")

    # Generate sitemap
    rows = conn.execute(
        "SELECT company_name, discovered_at FROM disclosures WHERE company_name IS NOT NULL AND company_name != ''"
    ).fetchall()
    sitemap = generate_sitemap_index(rows, slug_for_name)
    print(f"  Sitemap: {sitemap}")
