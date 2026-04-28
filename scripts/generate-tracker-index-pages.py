#!/usr/bin/env python3
"""
generate-tracker-index-pages.py
Generates group and country index pages for the ransomware tracker.

Group pages: /ransomware-tracker/group/<actor-slug>/index.html
Country pages: /ransomware-tracker/country/<country-code>/index.html

Run after generate-victim-pages.py (which populates the group/country data).
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
OUT_DIR    = Path.home() / "Downloads/binary-response-site" / "binary-response" / "ransomware-tracker"
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
    if s is None:
        return ""
    return (str(s)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#39;"))

def infer_sector(name):
    """Infer sector from company name keywords. Handles domain-only names by stripping TLDs."""
    if not name:
        return ""
    name = name.strip()
    # Strip trailing URL artifacts and amounts
    name = re.sub(r'https?://\S+', '', name)
    name = re.sub(r'\$\S+', '', name)
    name = re.sub(r'\b\d+[\d.,]*\s*(GB|MB|TB|KB)', '', name, flags=re.IGNORECASE)
    name = re.sub(r'DISCLOSED|<.*?>|&[a-z]+;', '', name)
    name = re.sub(r'\s+', ' ', name).strip()
    if not name:
        return ""

    n = name.lower()

    # Strip common TLDs and corporate suffixes to match on root domain / base name
    root = re.sub(r'\.(com|org|net|io|co|gov|edu|gov\.in|com\.br|com\.au|com\.hk|com\.cn|co\.uk|co\.za|co\.nz|co\.il|it|be|de|fr|es|nl|pl|ru|jp|kr|in|ca|ie|at|ch|se|no|dk|fi)\b.*$', '', n, flags=re.IGNORECASE)
    root = re.sub(r'\b(inc|llc|ltd|limited|gmbh|spa|s\.a|corp|corporation|plc|ag|co|holdings|group|holdings?|associates|services|enterprises?|solutions|international|partners|systems|technologies|consulting|advisors?)\b.*$', '', root)
    root = re.sub(r'[-\s]+', ' ', root).strip()

    all_text = n + ' ' + root
    # Education
    if any(k in all_text for k in ["university", "college", "school", "academy", "institute", "education", "learning", "training", "student", "campus", "nsw edu", "isd", "school district"]):
        return "Education"
    # Healthcare
    if any(k in all_text for k in ["hospital", "clinic", "health", "medical", "pharma", "dental", "care center", "healthcare", "clinical", "diagnostic", "laboratory", "lab ", "surgery", "urgic", "eye center", "dermatology", "orthopedic", "physiotherapy", "rehabilitation", "nursing", "senior care", "assisted living", "hospice"]):
        return "Healthcare"
    # Government
    if any(k in all_text for k in ["police", "gov", "government", "municipality", "county", "city of", "town of", "state of", "department", "agency", "courthouse", "judicial", "army", "navy", "air force", "defense", "military", "veterans", "irs", "tax", "licensing", "dmv", "permit", "regulatory", "port authority", "transit authority"]):
        return "Government"
    # Financial
    if any(k in all_text for k in ["bank", "finance", "financial", "credit", "investment", "insurance", "insurer", "wealth", "capital", "securities", "trading", "loan", "lending", "mortgage", "asset management", "hedge fund", "pension", "401k", "broker", "advisory", "accounting", "cpa", "tax"]):
        return "Financial Services"
    # Technology
    if any(k in all_text for k in ["tech", "software", "digital", "cyber", "cloud", "data center", "datacenter", "hosting", "saas", "it services", "it solution", "systems", "networks", "telecom", "telecommunications", "isp", "broadband", "fiber", "wireless", "satellite", "iot", "semiconductor", "chip", "electronics", "manufacturing", "ai ", "machine learning"]):
        return "Technology"
    # Critical Infrastructure / Energy
    if any(k in all_text for k in ["energy", "power", "electric", "utility", "gas", "oil", "petroleum", "pipeline", "refinery", "nuclear", "solar", "wind", "hydro", "grid", "water supply", "sewage", "wastewater", "infrastructure", "transportation", "railway", "railroad", "metro", "airline", "aviation", "airport", "port", "shipping", "logistics", "freight", "supply chain", "construction", "engineering"]):
        return "Critical Infrastructure"
    # Legal
    if any(k in all_text for k in ["law", "legal", "attorney", "advocate", "solicitor", "barrister", "counsel", "law firm", "legal services", "notary"]):
        return "Legal Services"
    # Manufacturing
    if any(k in all_text for k in ["manufacturing", "factory", "industrial", "machinery", "equipment", "parts", "components", "assembly", "production", "metal", "steel", "automotive", "aerospace", "defense contractor", "chemical", "textile", "pharmaceutical"]):
        return "Manufacturing"
    # Retail / Hospitality
    if any(k in all_text for k in ["retail", "store", "shop", "mall", "supermarket", "grocery", "restaurant", "hotel", "hospitality", "resort", "casino", "gaming", "entertainment", "theater", "cinema", "amusement", "tourism", "travel agency"]):
        return "Retail & Hospitality"
    # Real Estate / Construction
    if any(k in all_text for k in ["real estate", "property", "realty", "realtor", "brokerage", "construction", "contractor", "builder", "developer", "architecture", "architect", "engineering firm", "surveying"]):
        return "Real Estate & Construction"
    # Media / Professional Services
    if any(k in all_text for k in ["media", "publishing", "broadcast", "news", "journalism", "newspaper", "magazine", "radio", "television", "advertising", "marketing", "pr ", "public relations", "consulting", "advisory", "management", "outsourcing", "staffing", "recruitment", "headhunter", "professional services"]):
        return "Professional Services"
    # Agriculture
    if any(k in all_text for k in ["agriculture", "farming", "farm", "food processing", "beverage", "dairy", "livestock", "seed", "fertilizer", "agritech"]):
        return "Agriculture"
    # Non-profit
    if any(k in all_text for k in ["charity", "nonprofit", "non-profit", "ngo", "foundation", "religious", "church", "mosque", "synagogue", "temple", "faith", "community services", "social services", "humanitarian", "relief"]):
        return "Non-Profit"
    # Automotive
    if any(k in all_text for k in ["automotive", "auto dealer", "car dealership", "vehicle", "motor", "tire", "repair", "mechanic", "collision", "auto parts", "dealership"]):
        return "Automotive"
    # Consulting / Services
    if any(k in all_text for k in ["consulting", "consultancy", "advisory", "professional services", "outsourcing", "staffing", "recruitment", "headhunter", "project consulting", "management consulting", "business consulting"]):
        return "Professional Services"
    # Energy / Oil & Gas
    if any(k in all_text for k in ["oil", "petroleum", "energy", "gas", "refinery", "pipeline", " Aramco", " Shell", " Chevron", " Exxon", " BP ", " Lukoil", " petro", " drill", " upstream", " downstream", " oilfield"]):
        return "Energy"
    # Food & Beverage
    if any(k in all_text for k in ["food", "beverage", "restaurant", "cafe", "coffee", "dining", "catering", "brewery", "winery", "distillery", "meat", "seafood", "poultry", "dairy"]):
        return "Food & Beverage"
    # Furniture / Office
    if any(k in all_text for k in ["furniture", "office", "furnishings", "interior", "design", "decor"]):
        return "Furniture & Office"
    # Fashion / Apparel
    if any(k in all_text for k in ["fashion", "apparel", "clothing", "garment", "textile", "shoes", "footwear", "luxury", "boutique", "jewelry", "watch", "accessories"]):
        return "Fashion & Apparel"
    # Insurance
    if any(k in all_text for k in ["insurance", "insurer", "reinsurance", "underwriting", "assurance"]):
        return "Insurance"
    # Telecommunications
    if any(k in all_text for k in ["telecom", "wireless", "mobile", "cellular", "isp", "broadband", "satellite communications", "network provider"]):
        return "Telecommunications"
    # Aviation / Aerospace
    if any(k in all_text for k in ["aviation", "airline", "airways", "air cargo", "aerospace", "airport", "air force", "flight", "pilot", "jet", "aircraft", "pilatus", "emery air", "sky", "aerodrome"]):
        return "Aviation & Aerospace"
    # Security / Cybersecurity
    if any(k in all_text for k in ["security", "cybersecurity", "cyber defense", "infosec", "security solution", "security services", "protect", "defense"]):
        return "Security & Cybersecurity"
    # Cleaning / Facilities
    if any(k in all_text for k in ["cleaning", "clean", "janitorial", "facilities", "maintenance", "hvac", "plumbing", "electrical contractor", "mechanical contractor"]):
        return "Facilities Management"
    # Printing / Graphics
    if any(k in all_text for k in ["printing", "print", "graphics", "signage", "signs", "banner", "promotional", "branding"]):
        return "Printing & Graphics"
    # Environmental / Waste
    if any(k in all_text for k in ["environmental", "waste management", "recycling", "wastewater", "pollution", "remediation", "hazardous"]):
        return "Environmental Services"
    # Dental / Medical Supplies
    if any(k in all_text for k in ["dental", "optical", "vision", "eyecare", "lens", "optometry", "ophthalmology"]):
        return "Healthcare"
    # HVAC / Building Systems
    if any(k in all_text for k in ["hvac", "heating", "ventilation", "air conditioning", "refrigeration", "cold chain", "mechanical"]):
        return "Building Systems"
    # Procurement / Trading
    if any(k in all_text for k in ["trading", "trader", "commodities", "exporter", "importer", "supply", "procurement", "distributor"]):
        return "Trading & Distribution"
    # Research / Lab Testing
    if any(k in all_text for k in ["research", "laboratory", "testing", "lab ", "lab.", "analytical", "qc ", "quality control", "r&d"]):
        return "Research & Testing"
    # Parking / Transportation Services
    if any(k in all_text for k in ["parking", "transportation", "transit", "shuttle", "bus", "metro", "railway", "railroad"]):
        return "Transportation"
    # Architecture / Interior Design
    if any(k in all_text for k in ["architecture", "architect", "interior design", "interior", "space planning", "fit-out"]):
        return "Real Estate & Construction"
    # Music / Audio / Events
    if any(k in all_text for k in ["music", "audio", "sound", "recording", "studio", "event", "concerts", "ticketing"]):
        return "Entertainment & Arts"
    # Sports / Fitness / Recreation
    if any(k in all_text for k in ["fitness", "gym", "sports", "athletic", "recreation", "club", "wellness", "spa"]):
        return "Sports & Recreation"
    # Hotels / Resorts / Hospitality
    if any(k in all_text for k in ["hotel", "resort", "inn", "suites", "hospitality", "lodge", "motel", "accommodation"]):
        return "Retail & Hospitality"
    # Film / Photography / Media Production
    if any(k in all_text for k in ["film", "photography", "photo", "camera", "production company", "post-production"]):
        return "Entertainment & Arts"
    # Agriculture / Forestry
    if any(k in all_text for k in ["forestry", "timber", "wood", "paper", "pulp", "logging"]):
        return "Agriculture & Forestry"
    # Parking / Auto Services
    if any(k in all_text for k in ["collision", "auto body", "body shop", "tire", "tires", "mechanic", "auto repair", "automotive"]):
        return "Automotive"
    # Mining / Resources
    if any(k in all_text for k in ["mining", "minerals", "extraction", "quarry", "aggregates", "cement", "limestone", "gold", "copper", "coal", "oilfield", "petro"]):
        return "Mining & Resources"
    # Marine / Nautical
    if any(k in all_text for k in ["marine", "naval", "ship", "yacht", "vessel", "port", "harbor", "maritime", "boat", "sailing", "ferry", "coast guard"]):
        return "Marine & Maritime"
    # Veterinary / Animal
    if any(k in all_text for k in ["veterinary", "vet ", "clinic", "animal", "pet ", "zoo", "equine", "livestock", "breed", "horse", "cattle"]):
        return "Veterinary & Animal Services"
    # Surveying / Engineering
    if any(k in all_text for k in ["surveying", "surveyor", "geomatics", "geospatial", "cartography", "mapping"]):
        return "Surveying & Engineering"
    # Dance / Entertainment / Arts
    if any(k in all_text for k in ["dance", "ballet", "theater", "theatre", "performing arts", "cinema", "film", "production", "studio", "media", "entertainment", "event", "venue", "amphitheater"]):
        return "Entertainment & Arts"
    # Accounting / Bookkeeping
    if any(k in all_text for k in ["accounting", "accountant", "bookkeeping", "cpa", "tax preparation", "payroll", "audit"]):
        return "Accounting & Bookkeeping"
    # HR / Workforce
    if any(k in all_text for k in ["human resources", "hr ", "workforce", "people operations", "talent", "labor", "employment"]):
        return "Human Resources"
    return ""

def region_name(code):
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
        "PT":"Portugal","GR":"Greece","CL":"Chile","EC":"Ecuador","PA":"Panama",
        "PR":"Puerto Rico","CR":"Costa Rica","SK":"Slovakia","HU":"Hungary",
        "RS":"Serbia","BG":"Bulgaria","HR":"Croatia","SI":"Slovenia",
        "LT":"Lithuania","EE":"Estonia","LV":"Latvia","IS":"Iceland",
        "LU":"Luxembourg","MT":"Malta","CY":"Cyprus","GE":"Georgia",
        "AM":"Armenia","AZ":"Azerbaijan","KZ":"Kazakhstan","BD":"Bangladesh",
        "PK":"Pakistan","LK":"Sri Lanka","NP":"Nepal","MM":"Myanmar",
        "KH":"Cambodia","LA":"Laos","FJ":"Fiji","PG":"Papua New Guinea",
        "KE":"Kenya","GH":"Ghana","MA":"Morocco","DZ":"Algeria","TN":"Tunisia",
        "LB":"Lebanon","JO":"Jordan","IQ":"Iraq","IR":"Iran","QA":"Qatar",
        "KW":"Kuwait","BH":"Bahrain","OM":"Oman","YE":"Yemen","GT":"Guatemala",
        "BZ":"Belize","HN":"Honduras","SV":"El Salvador","NI":"Nicaragua",
        "VE":"Venezuela","BO":"Bolivia","PY":"Paraguay","UY":"Uruguay",
        "GY":"Guyana","SR":"Suriname",
    }
    return MAP.get(code, code or "Unknown")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# ── Group page ────────────────────────────────────────────────────────────────

GROUP_DESCRIPTIONS = {
    "lockbit3": "LockBit 3.0 is a prolific Ransomware-as-a-Service (RaaS) operation known for exfiltrating large volumes of sensitive data before encrypting victim networks.",
    "lockbit2": "LockBit 2.0 is a RaaS operation that operated globally, known for rapid encryption and double-extortion tactics.",
    "akira": "Akira is a RaaS group that emerged in 2023, targeting organizations worldwide with double-extortion tactics.",
    "ransomhub": "RansomHub is a RaaS group active since 2024, known for targeting critical infrastructure sectors.",
    "play": "Play (aka PlayCrypt) is a RaaS group that has targeted healthcare, education, and infrastructure organizations.",
    "alphv": "ALPHV (BlackCat) is a sophisticated RaaS group known for custom tooling and high-profile attacks.",
    "bianlian": "BianLian is a RaaS group known for double-extortion, primarily targeting education, healthcare, and critical infrastructure.",
    "clop": "Clop (ClOp) is a RaaS group known for exploiting vulnerabilities like GoAnywhere and MOVEit to compromise hundreds of organizations.",
    "rhysida": "Rhysida is a RaaS group that emerged in 2023, known for targeting education, healthcare, and government sectors.",
    "blackbasta": "Black Basta is a RaaS group that has targeted critical infrastructure, manufacturing, and healthcare.",
}

def build_group_page(group_name, victims, total_count):
    display_name = group_name  # Already slugified if from DB
    slug = slugify(group_name)
    group_url = f"{TRACKER_URL}/group/{quote(slug)}/index.html"
    canonical_url = group_url

    # Build victim list items
    items = []
    for v in victims[:100]:  # Cap at 100 for performance
        name = v["company_name"] or "Unknown"
        v_slug = slugify(name)
        v_url = f"{TRACKER_URL}/victim/{v_slug}.html"
        disc = (v["disclosure_date"] or "")[:10] if v["disclosure_date"] else "Unknown date"
        sector = v["sector"] or ""
        items.append(
            f'      <li class="victim-list-item">'
            f'<a href="{v_url}" class="victim-name">{esc(name)}</a>'
            f'<span class="victim-meta">{esc(sector)} — {disc}</span>'
            f'</li>'
        )
    items_str = "\n".join(items)
    count = len(victims)
    description = GROUP_DESCRIPTIONS.get(slug, f"{display_name} is a ransomware group that has targeted organizations worldwide.")

    # Sector breakdown
    sectors = {}
    for v in victims:
        s = v["sector"] or "Unknown"
        sectors[s] = sectors.get(s, 0) + 1
    sector_bars = []
    if sectors:
        top_sectors = sorted(sectors.items(), key=lambda x: -x[1])[:5]
        for s, c in top_sectors:
            pct = int(c / count * 100)
            sector_bars.append(
                f'        <div class="sector-bar">'
                f'<span class="sector-name">{esc(s)}</span>'
                f'<div class="sector-track"><div class="sector-fill" style="width:{pct}%"></div></div>'
                f'<span class="sector-count">{c}</span>'
                f'</div>'
            )
    sector_html = "<div class='sector-breakdown'><h3>Top Sectors</h3>\n" + "\n".join(sector_bars) + "\n      </div>" if sector_bars else ""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>{esc(display_name)} Ransomware Group | {count} Victims | Binary Response</title>
<meta name="description" content="{count} victims of {display_name} ransomware. {description}">
<link rel="canonical" href="{canonical_url}">
<meta property="og:title" content="{esc(display_name)} Ransomware Victims">
<meta property="og:description" content="{count} organisations listed by {display_name}.">
<meta property="og:url" content="{canonical_url}">
<meta property="og:type" content="website">
<link rel="stylesheet" href="/css/style.css">
<style>
.group-hero {{background:linear-gradient(135deg,#0f1923 0%,#1a0a0a 100%);border-bottom:1px solid rgba(224,85,85,0.2);padding:3rem 0;margin-bottom:2rem}}
.group-hero h1 {{font-size:clamp(1.8rem,3.5vw,2.8rem);color:#fff;margin:0 0 0.5rem}}
.group-hero .subtitle {{color:#e05555;font-size:1rem;font-family:'JetBrains Mono',monospace}}
.group-count {{color:rgba(255,255,255,0.5);margin-top:0.5rem;font-size:0.9rem}}
.victim-list {{list-style:none;padding:0;margin:0}}
.victim-list-item {{display:flex;justify-content:space-between;align-items:center;padding:0.75rem 1rem;border-bottom:1px solid rgba(255,255,255,0.05);gap:1rem}}
.victim-list-item:hover {{background:rgba(255,255,255,0.03)}}
.victim-name {{color:#7eb3e0;text-decoration:none;font-size:0.95rem}}
.victim-name:hover {{text-decoration:underline}}
.victim-meta {{color:#556677;font-size:0.8rem;white-space:nowrap;font-family:'JetBrains Mono',monospace}}
.sector-breakdown {{background:#0f1923;border:1px solid #1e3a5f;border-radius:8px;padding:1.5rem;margin:2rem 0}}
.sector-breakdown h3 {{color:#7eb3e0;margin:0 0 1rem;font-size:0.9rem;text-transform:uppercase;letter-spacing:1px}}
.sector-bar {{display:grid;grid-template-columns:1fr 200px 50px;gap:0.75rem;align-items:center;margin-bottom:0.6rem}}
.sector-name {{color:#ccd8e0;font-size:0.85rem}}
.sector-track {{height:6px;background:#1e3a5f;border-radius:3px;overflow:hidden}}
.sector-fill {{height:100%;background:#e05555;border-radius:3px}}
.sector-count {{color:#e05555;font-size:0.8rem;font-family:'JetBrains Mono',monospace;text-align:right}}
.breadcrumbs {{padding:1rem 0;font-size:0.85rem;color:#556677}}
.breadcrumbs a {{color:#7eb3e0;text-decoration:none}}
.breadcrumbs a:hover {{text-decoration:underline}}
.container {{max-width:900px;margin:0 auto;padding:0 1.5rem}}
</style>
</head>
<body>
<nav class="site-nav"><a href="/index.html" class="nav-brand"><img src="/img/logo-icon.webp" alt="Binary Response" class="nav-logo" width="32" height="32"><span class="nav-name">Binary Response</span></a><button class="nav-toggle" aria-label="Menu"><span></span><span></span><span></span></button><div class="nav-links"></div></nav>

<div class="group-hero">
  <div class="container">
    <nav class="breadcrumbs">
      <a href="/index.html">Home</a> /
      <a href="/ransomware-tracker/">Ransomware Tracker</a> /
      <span>Groups</span> /
      <span>{esc(display_name)}</span>
    </nav>
    <h1>{esc(display_name)}</h1>
    <p class="subtitle">// Ransomware Group</p>
    <p class="group-count">{count} victim{'s' if count != 1 else ''} — {description}</p>
  </div>
</div>

<div class="container">
  <div class="section">
{sector_html}
    <h2 class="section-title">All Victims</h2>
    <ul class="victim-list">
{items_str}
    </ul>
    {'<p style="color:#556677;margin-top:1rem">Showing latest 100 of ' + str(count) + '</p>' if count > 100 else ''}
  </div>
</div>

<footer class="site-footer"><div class="container"><p style="opacity:0.6;font-size:0.85rem">&copy; Binary Response Ltd. All rights reserved.</p></div></footer>
<script src="/js/footer.js"></script><script src="/js/nav.js"></script>
</body>
</html>"""

# ── Country page ──────────────────────────────────────────────────────────────

def build_country_page(country_code, victims, total_count):
    country_name = region_name(country_code)
    country_url = f"{TRACKER_URL}/country/{quote(country_code)}/index.html"
    canonical_url = country_url

    items = []
    for v in victims[:100]:
        name = v["company_name"] or "Unknown"
        v_slug = slugify(name)
        v_url = f"{TRACKER_URL}/victim/{v_slug}.html"
        sector = v["sector"] or infer_sector(name)
        disc = (v["disclosure_date"] or "")[:10] if v["disclosure_date"] else "Unknown"
        items.append(
            f'      <li class="victim-list-item">'
            f'<a href="{v_url}" class="victim-name">{esc(name)}</a>'
            f'<span class="victim-meta">{esc(sector)} — {disc}</span>'
            f'</li>'
        )
    items_str = "\n".join(items)
    count = len(victims)

    # Sector breakdown
    sectors = {}
    for v in victims:
        s = v["sector"] or "Unknown"
        sectors[s] = sectors.get(s, 0) + 1
    sector_bars = []
    if sectors:
        top_sectors = sorted(sectors.items(), key=lambda x: -x[1])[:5]
        for s, c in top_sectors:
            pct = int(c / count * 100)
            sector_bars.append(
                f'        <div class="sector-bar">'
                f'<span class="sector-name">{esc(s)}</span>'
                f'<div class="sector-track"><div class="sector-fill" style="width:{pct}%"></div></div>'
                f'<span class="sector-count">{c}</span>'
                f'</div>'
            )
    sector_html = "<div class='sector-breakdown'><h3>Top Sectors</h3>\n" + "\n".join(sector_bars) + "\n      </div>" if sector_bars else ""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>{esc(country_name)} Ransomware Victims | {count} Companies | Binary Response</title>
<meta name="description" content="{count} ransomware victims from {country_name}. Browse all organisations listed by ransomware groups targeting {country_name}.">
<link rel="canonical" href="{canonical_url}">
<meta property="og:title" content="{esc(country_name)} Ransomware Victims">
<meta property="og:description" content="{count} organisations from {country_name} listed by ransomware groups.">
<meta property="og:url" content="{canonical_url}">
<meta property="og:type" content="website">
<link rel="stylesheet" href="/css/style.css">
<style>
.country-hero {{background:linear-gradient(135deg,#0f1923 0%,#0a1a2e 100%);border-bottom:1px solid rgba(126,179,224,0.2);padding:3rem 0;margin-bottom:2rem}}
.country-hero h1 {{font-size:clamp(1.8rem,3.5vw,2.8rem);color:#fff;margin:0 0 0.5rem}}
.country-hero .subtitle {{color:#7eb3e0;font-size:1rem;font-family:'JetBrains Mono',monospace}}
.country-count {{color:rgba(255,255,255,0.5);margin-top:0.5rem;font-size:0.9rem}}
.victim-list {{list-style:none;padding:0;margin:0}}
.victim-list-item {{display:flex;justify-content:space-between;align-items:center;padding:0.75rem 1rem;border-bottom:1px solid rgba(255,255,255,0.05);gap:1rem}}
.victim-list-item:hover {{background:rgba(255,255,255,0.03)}}
.victim-name {{color:#7eb3e0;text-decoration:none;font-size:0.95rem}}
.victim-name:hover {{text-decoration:underline}}
.victim-meta {{color:#556677;font-size:0.8rem;white-space:nowrap;font-family:'JetBrains Mono',monospace}}
.breadcrumbs {{padding:1rem 0;font-size:0.85rem;color:#556677}}
.breadcrumbs a {{color:#7eb3e0;text-decoration:none}}
.breadcrumbs a:hover {{text-decoration:underline}}
.container {{max-width:900px;margin:0 auto;padding:0 1.5rem}}
.section-title {{color:#7eb3e0;font-size:1.2rem;margin:2rem 0 1rem;border-bottom:1px solid rgba(126,179,224,0.15);padding-bottom:0.5rem}}
</style>
</head>
<body>
<nav class="site-nav"><a href="/index.html" class="nav-brand"><img src="/img/logo-icon.webp" alt="Binary Response" class="nav-logo" width="32" height="32"><span class="nav-name">Binary Response</span></a><button class="nav-toggle" aria-label="Menu"><span></span><span></span><span></span></button><div class="nav-links"></div></nav>

<div class="country-hero">
  <div class="container">
    <nav class="breadcrumbs">
      <a href="/index.html">Home</a> /
      <a href="/ransomware-tracker/">Ransomware Tracker</a> /
      <span>Countries</span> /
      <span>{esc(country_name)}</span>
    </nav>
    <h1>{esc(country_name)}</h1>
    <p class="subtitle">// Country</p>
    <p class="country-count">{count} victim{'s' if count != 1 else ''}</p>
  </div>
</div>

<div class="container">
  <div class="section">
{sector_html}
    <h2 class="section-title">All Victims in {esc(country_name)}</h2>
    <ul class="victim-list">
{items_str}
    </ul>
    {'<p style="color:#556677;margin-top:1rem">Showing latest 100 of ' + str(count) + '</p>' if count > 100 else ''}
  </div>
</div>

<footer class="site-footer"><div class="container"><p style="opacity:0.6;font-size:0.85rem">&copy; Binary Response Ltd. All rights reserved.</p></div></footer>
<script src="/js/footer.js"></script><script src="/js/nav.js"></script>
</body>
</html>"""


# ── Main ──────────────────────────────────────────────────────────────────────

def main(dry_run=False):
    conn = get_db()

    # Ensure directories
    group_dir = OUT_DIR / "group"
    country_dir = OUT_DIR / "country"
    if not dry_run:
        group_dir.mkdir(parents=True, exist_ok=True)
        country_dir.mkdir(parents=True, exist_ok=True)

    # ── Generate group pages ────────────────────────────────────────────────
    rows = conn.execute("""
        SELECT company_name, threat_actor, sector, region, disclosure_date
        FROM disclosures
        WHERE company_name IS NOT NULL
        AND company_name != ''
        AND threat_actor IS NOT NULL
        AND threat_actor != ''
    """).fetchall()

    # Group by actor
    groups = {}
    for r in rows:
        actor = r["threat_actor"]
        groups.setdefault(actor, []).append(dict(r))

    group_created = 0
    for actor, victims in groups.items():
        slug = slugify(actor)
        actor_dir = group_dir / slug
        out_path = actor_dir / "index.html"

        if dry_run:
            print(f"[dry-run] would create {out_path} ({len(victims)} victims)")
        else:
            actor_dir.mkdir(parents=True, exist_ok=True)
            html = build_group_page(actor, victims, len(victims))
            out_path.write_text(html, encoding="utf-8")
            print(f"Created {out_path} ({len(victims)} victims)")
        group_created += 1

    # ── Generate country pages ──────────────────────────────────────────────
    rows2 = conn.execute("""
        SELECT company_name, threat_actor, sector, region, disclosure_date
        FROM disclosures
        WHERE company_name IS NOT NULL
        AND company_name != ''
        AND region IS NOT NULL
        AND region != ''
    """).fetchall()

    countries = {}
    for r in rows2:
        region = r["region"]
        countries.setdefault(region, []).append(dict(r))

    country_created = 0
    for region, victims in countries.items():
        out_path = country_dir / region / "index.html"

        if dry_run:
            print(f"[dry-run] would create {out_path} ({len(victims)} victims)")
        else:
            (country_dir / region).mkdir(parents=True, exist_ok=True)
            html = build_country_page(region, victims, len(victims))
            out_path.write_text(html, encoding="utf-8")
            print(f"Created {out_path} ({len(victims)} victims)")
        country_created += 1

    print(f"\nDone: {group_created} group pages, {country_created} country pages created" +
          (" [dry-run]" if dry_run else ""))
    return 0


if __name__ == "__main__":
    import sys
    dry_run = "--dry-run" in sys.argv
    sys.exit(main(dry_run=dry_run))
