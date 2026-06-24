"""Capture live state of CISO Assistant platform + take screenshots of Helix data."""
import asyncio
import base64
import json
import os
import subprocess
import urllib.request
import ssl
from pathlib import Path

from playwright.async_api import async_playwright

ENV_PATH = Path("/Users/ifeanyi/Documents/IfeSec/Tools/ciso-assistant-community/cli/.mcp.env")
PROJECT_DIR = Path("/Users/ifeanyi/Documents/IfeSec/Projects/helix-health-grc-sandbox")
USER = "ijeziermf@gmail.com"
PW = base64.b64decode("ODk1MEZvdXJ0aA==").decode()
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

auth_tok = subprocess.run(
    ["bash", "-c", f"source {ENV_PATH} && echo $TOKEN"],
    capture_output=True, text=True, timeout=10,
).stdout.strip()

ctx = ssl._create_unverified_context()


def api_get(path):
    req = urllib.request.Request(
        f"https://localhost:8443{path}",
        headers={"Authorization": f"Token {auth_tok}", "Accept": "application/json"},
    )
    return json.loads(urllib.request.urlopen(req, context=ctx, timeout=10).read())


def export_helix_state():
    """Dump all Helix-tagged objects to JSON for the report."""
    print("\n=== EXPORT HELIX LIVE STATE ===")
    state = {}

    # Perimeters (filter to Helix folder)
    folders = api_get("/api/folders/?limit=100")
    helix_folder = next(
        (f for f in folders.get("results", []) if f.get("name") == "Helix Health"),
        None,
    )
    if not helix_folder:
        print("  Helix folder not found!")
        return

    folder_id = helix_folder["id"]
    perimeters_all = api_get("/api/perimeters/?limit=100")
    perimeters = [p for p in perimeters_all.get("results", []) if p.get("folder", {}).get("id") == folder_id]
    state["folder"] = helix_folder
    state["perimeters"] = perimeters
    print(f"  Helix folder: {helix_folder['id'][:8]}")
    print(f"  Perimeters: {len(perimeters)}")

    risks_all = api_get("/api/risk-scenarios/?limit=100")
    risks = [r for r in risks_all.get("results", []) if r.get("folder", {}).get("id") == folder_id]
    state["risk_scenarios"] = risks
    print(f"  Risk scenarios: {len(risks)}")

    policies_all = api_get("/api/policies/?limit=100")
    policies = [p for p in policies_all.get("results", []) if p.get("folder", {}).get("id") == folder_id]
    state["policies"] = policies
    print(f"  Policies: {len(policies)}")

    entities_all = api_get("/api/entities/?limit=100")
    entities = [e for e in entities_all.get("results", []) if e.get("folder", {}).get("id") == folder_id]
    state["entities"] = entities
    print(f"  Entities: {len(entities)}")

    contracts_all = api_get("/api/contracts/?limit=100")
    helix_contracts = [c for c in contracts_all.get("results", []) if c.get("folder", {}).get("id") == folder_id]
    state["contracts"] = helix_contracts
    print(f"  Contracts: {len(helix_contracts)}")

    matrices_all = api_get("/api/risk-matrices/?limit=100")
    helix_matrices = [m for m in matrices_all.get("results", []) if m.get("name") == "Helix 5x5 ISO-27005"]
    state["risk_matrices"] = helix_matrices
    print(f"  Risk matrices: {len(helix_matrices)}")

    assessments_all = api_get("/api/risk-assessments/?limit=100")
    helix_assessments = [a for a in assessments_all.get("results", []) if a.get("folder", {}).get("id") == folder_id]
    state["risk_assessments"] = helix_assessments
    print(f"  Risk assessments: {len(helix_assessments)}")

    # Frameworks (HIPAA + HDS + SOC 2)
    libraries_all = api_get("/api/loaded-libraries/?limit=100")
    helix_libraries = [
        l for l in libraries_all.get("results", [])
        if any(k in (l.get("name", "") + l.get("urn", "")).lower() for k in ["hipaa", "hds", "hitrust", "soc2"])
    ]
    state["frameworks"] = helix_libraries
    print(f"  Frameworks (HIPAA/HDS/SOC2): {len(helix_libraries)}")
    # HITRUST is NOT in v3.18.3 catalog - document this
    state["hitrust_available"] = False
    state["hitrust_note"] = "HITRUST CSF v11 not in CISO Assistant v3.18.3 catalog. HIPAA mapped via NIST SP-800-66 rev2 reference. Recommend custom JSON upload for HITRUST CSF if needed."

    out_path = PROJECT_DIR / "helix_live_state.json"
    with open(out_path, "w") as f:
        json.dump(state, f, indent=2)
    print(f"\n✓ Saved: {out_path}")
    return state


async def capture_screenshots():
    """Login and capture screenshots of each major page with Helix data."""
    print("\n=== CAPTURE SCREENSHOTS ===")
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            executable_path=CHROME,
            args=["--no-sandbox", "--ignore-certificate-errors", "--disable-dev-shm-usage"],
        )
        context = await browser.new_context(ignore_https_errors=True, viewport={"width": 1440, "height": 900})
        page = await context.new_page()

        # Login
        await page.goto("https://localhost:8443/login", wait_until="networkidle", timeout=30000)
        await page.fill('input[name="username"], input[type="email"]', USER)
        await page.fill('input[name="password"], input[type="password"]', PW)
        await page.click('button[type="submit"]')
        await page.wait_for_url(lambda url: "/login" not in url, timeout=15000)
        print(f"  Logged in, at: {page.url}")

        pages = [
            ("/analytics", "analytics"),
            ("/risk-scenarios", "risks"),
            ("/policies", "policies"),
            ("/perimeters", "perimeters"),
            ("/folders", "folders"),
            ("/frameworks", "frameworks"),
            ("/entities", "entities"),
            ("/risk-assessments", "risk-assessments"),
            ("/contracts", "contracts"),
            ("/risk-matrices", "risk-matrices"),
        ]
        for path, fname in pages:
            try:
                await page.goto(f"https://localhost:8443{path}", wait_until="networkidle", timeout=15000)
                await page.wait_for_timeout(3500)
                # Full page screenshot
                await page.screenshot(path=f"/tmp/helix-final-{fname}.png", full_page=True)
                # Get body text length to verify rendering
                text_len = len(await page.evaluate("document.body.innerText"))
                rows = await page.evaluate("document.querySelectorAll('table tr, [role=row]').length")
                print(f"  {path:<25} -> /tmp/helix-final-{fname}.png (text={text_len}, rows={rows})")
            except Exception as e:
                print(f"  {path:<25} FAILED: {str(e)[:100]}")

        await browser.close()


async def main():
    state = export_helix_state()
    await capture_screenshots()
    print("\n=== FINAL COUNTS ===")
    print(f"  Perimeters:    {len(state['perimeters'])}")
    print(f"  Risk scenarios:{len(state['risk_scenarios'])}")
    print(f"  Policies:      {len(state['policies'])}")
    print(f"  Entities:      {len(state['entities'])}")
    print(f"  Contracts:     {len(state['contracts'])}")
    print(f"  Frameworks:    {len(state['frameworks'])}")
    print(f"  Risk assessment: {len(state['risk_assessments'])}")
    print(f"  Risk matrix:   {len(state['risk_matrices'])}")


asyncio.run(main())