#!/usr/bin/env python3
"""
update-ransomware-tracker.py
Combined generator + deployer for the ransomware tracker site.
Regenerates victim pages, group/country index pages, sitemap, and deploys to IONOS.

Usage:
  python3 update-ransomware-tracker.py --all      # Full regeneration + deploy
  python3 update-ransomware-tracker.py --recent   # New victims only + deploy
"""

import subprocess, sys
from pathlib import Path

SCRIPT_DIR = Path.home() / "Downloads/binary-response-site" / "binary-response"
SCRIPTS    = SCRIPT_DIR / "scripts"
VICTIM_SPY = SCRIPTS / "generate-victim-pages.py"
INDEX_SPY  = SCRIPTS / "generate-tracker-index-pages.py"
SITEMAP_SP = SCRIPTS / "generate-tracker-sitemap.py"

IONOS_HOST  = "su296924@access-5019920255.webspace-host.com"
IONOS_BASE  = "public/ransomware-tracker"
REMOTE      = f"{IONOS_HOST}:{IONOS_BASE}"
LOCAL_BASE  = SCRIPT_DIR / "ransomware-tracker"

# Password from ~/.hermes/secrets/ionos_sftp_password
PASS_FILE = Path.home() / ".hermes" / "secrets" / "ionos_sftp_password"
PASS      = PASS_FILE.read_text().strip()

def sshpass(cmd):
    return f"sshpass -p {PASS!r} {cmd}"

def run(label, cmd, timeout=300, env=None):
    print(f"\n=== {label} ===")
    result = subprocess.run(cmd, shell=True, capture_output=False, timeout=timeout, env=env)
    if result.returncode != 0:
        print(f"ERROR in {label} — exit {result.returncode}")
        sys.exit(result.returncode)
    print(f"Done: {label}")

def rsync(src, dst):
    import os
    env = os.environ.copy()
    env["SSHPASS"] = PASS
    cmd = f"rsync -avz -e 'sshpass -e ssh -o StrictHostKeyChecking=no' {src} {dst}"
    run(f"rsync {src} → {dst}", cmd, env=env)

def main():
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--all",    action="store_true", help="Full regeneration (all victims)")
    p.add_argument("--recent",  action="store_true", help="Recent victims only (last 7 days)")
    p.add_argument("--deploy", action="store_true", default=True, help="Deploy to IONOS (default: True)")
    p.add_argument("--no-deploy", dest="deploy", action="store_false", help="Skip deployment")
    args = p.parse_args()

    if not (args.all or args.recent):
        print("Specify --all or --recent")
        sys.exit(1)

    mode = "--all" if args.all else "--recent"
    recent_tag = " (recent only)" if args.recent else ""

    # 1. Generate victim pages
    run("Generate victim pages", f"cd {SCRIPTS} && python3 generate-victim-pages.py {mode}")

    # 2. Generate group/country index pages
    run("Generate index pages", f"cd {SCRIPTS} && python3 generate-tracker-index-pages.py")

    # 3. Generate sitemap
    if SITEMAP_SP.exists():
        run("Generate sitemap", f"cd {SCRIPTS} && python3 generate-tracker-sitemap.py")

    if not args.deploy:
        print("\n=== Deploy skipped ===")
        return

    # 4. Deploy victim pages (large, do first)
    rsync(
        f"{LOCAL_BASE}/victim/",
        f"{IONOS_HOST}:{IONOS_BASE}/victim/"
    )

    # 5. Deploy group pages
    rsync(
        f"{LOCAL_BASE}/group/",
        f"{IONOS_HOST}:{IONOS_BASE}/group/"
    )

    # 6. Deploy country pages
    rsync(
        f"{LOCAL_BASE}/country/",
        f"{IONOS_HOST}:{IONOS_BASE}/country/"
    )

    # 7. Deploy sitemap
    if SITEMAP_SP.exists():
        rsync(
            f"{LOCAL_BASE}/sitemap.xml",
            f"{IONOS_HOST}:{IONOS_BASE}/sitemap.xml"
        )

    print("\n=== All done ===")

if __name__ == "__main__":
    main()
