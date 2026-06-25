#!/usr/bin/env python3
"""
Helix Portfolio Live Dashboard Generator.

Fetches live state from CISO Assistant API and produces a self-contained
HTML dashboard. Designed to run as a no_agent cron every 5 minutes.
"""
import asyncio
import base64
import json
import os
import ssl
import subprocess
import urllib.request
from datetime import datetime
from pathlib import Path

ENV = "/Users/ifeanyi/Documents/IfeSec/Tools/ciso-assistant-community/cli/.mcp.env"
OUT = Path("/Users/ifeanyi/Documents/IfeSec/Projects/helix-health-grc-sandbox/dashboards/mission-control.html")


def get_token() -> str:
    """Load PAT from .mcp.env without exposing it inline."""
    result = subprocess.run(
        ["bash", "-c", f"source {ENV} && echo $TOKEN"],
        capture_output=True, text=True, timeout=10,
    )
    tok = result.stdout.strip()
    if not tok:
        raise RuntimeError(f"No TOKEN in {ENV}")
    return tok


def api_get(path: str) -> dict:
    """Curl CISO Assistant API and return parsed JSON."""
    token = get_token()
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    req = urllib.request.Request(
        f"https://localhost:8443{path}",
        headers={"Authorization": f"Token {token}"},
    )
    with urllib.request.urlopen(req, context=ctx, timeout=15) as r:
        return json.loads(r.read())


def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)

    # Fetch live counts
    helix_folder_id = None
    folders = api_get("/api/folders/?limit=100").get("results", [])
    for f in folders:
        if f["name"] == "Helix Health":
            helix_folder_id = f["id"]
            break

    if not helix_folder_id:
        # Fallback: search by content
        all_folders = api_get("/api/folders/?limit=200").get("results", [])
        helix_folder_id = next((f["id"] for f in all_folders if "Helix" in f.get("name", "")), None)

    counts = {
        "perimeters": 0,
        "risks": 0,
        "policies": 0,
        "vendors": 0,
        "contracts": 0,
        "frameworks": 0,
        "assessments": 0,
        "matrices": 0,
        "processings": 0,
        "validation_flows": 0,
    }

    def count_in_folder(endpoint: str, folder_id: str) -> int:
        """Fetch all records and count those whose folder.id matches."""
        data = api_get(f"/api/{endpoint}/?limit=200")
        n = 0
        for r in data.get("results", []):
            f = r.get("folder")
            if isinstance(f, dict) and f.get("id") == folder_id:
                n += 1
            elif isinstance(f, str) and f == folder_id:
                n += 1
        return n


    if helix_folder_id:
        counts["perimeters"] = count_in_folder("perimeters", helix_folder_id)
        counts["risks"] = count_in_folder("risk-scenarios", helix_folder_id)
        counts["policies"] = count_in_folder("policies", helix_folder_id)
        counts["vendors"] = count_in_folder("entities", helix_folder_id)
        counts["contracts"] = count_in_folder("contracts", helix_folder_id)
        counts["assessments"] = count_in_folder("risk-assessments", helix_folder_id)
        counts["matrices"] = count_in_folder("risk-matrices", helix_folder_id)
        counts["processings"] = count_in_folder("privacy/processings", helix_folder_id)
        counts["validation_flows"] = count_in_folder("validation-flows", helix_folder_id)

    # Frameworks are global
    libs = api_get("/api/loaded-libraries/?limit=100").get("results", [])
    helix_libs = [
        l for l in libs
        if any(k in (l.get("name") or "").lower() for k in ["hipaa", "hds", "soc 2", "soc2", "nist csf", "iso 27001"])
    ]
    counts["frameworks"] = len(helix_libs) if helix_libs else len(libs)

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S EDT")

    cards = [
        ("Perimeters", counts["perimeters"], "PHI-scope systems"),
        ("Risk Scenarios", counts["risks"], "12-sector + 6 AtlasPay"),
        ("Policies", counts["policies"], "HIPAA-aligned"),
        ("Vendors (BAA)", counts["vendors"], "TPRM-tracked"),
        ("Contracts", counts["contracts"], "Linked to vendors"),
        ("Frameworks", counts["frameworks"], "HIPAA + HDS + SOC 2 + NIST + ISO"),
        ("Risk Assessment", counts["assessments"], "Active"),
        ("Risk Matrices", counts["matrices"], "5x5 ISO-27005"),
        ("ROPA Processings", counts["processings"], "HIPAA processing activities"),
        ("Validation Flows", counts["validation_flows"], "Approver workflows"),
    ]

    cards_html = "\n".join(
        f'<div class="card"><div class="num">{n}</div><div class="lbl">{lbl}</div><div class="sub">{sub}</div></div>'
        for lbl, n, sub in cards
    )

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta http-equiv="refresh" content="300">
<title>IfeSec Mission Control — Helix Portfolio</title>
<style>
:root {{ --gold: #d4af37; --crimson: #8b0000; --bg: #0a0e1a; --card: #141925; --border: #1f2937; --text: #e8e8e8; --muted: #6b7785; }}
*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:var(--bg);color:var(--text);font-family:-apple-system,BlinkMacSystemFont,'SF Pro Display',sans-serif;padding:24px;min-height:100vh}}
.header{{background:linear-gradient(135deg,#0d1320 0%,#111a2e 100%);border-bottom:1px solid var(--border);padding:24px 32px;border-radius:8px;margin-bottom:24px}}
.header h1{{font-size:24px;font-weight:700;color:var(--gold);margin-bottom:4px}}
.header p{{color:var(--muted);font-size:13px}}
.grid{{display:grid;grid-template-columns:repeat(5,1fr);gap:12px;margin-bottom:24px}}
.card{{background:var(--card);border:1px solid var(--border);border-radius:8px;padding:16px;border-left:3px solid var(--gold)}}
.card .num{{font-size:28px;font-weight:700;color:var(--gold)}}
.card .lbl{{font-size:12px;color:var(--text);margin-top:4px;font-weight:600}}
.card .sub{{font-size:10px;color:var(--muted);margin-top:2px;text-transform:uppercase;letter-spacing:0.5px}}
.footer{{text-align:center;color:var(--muted);font-size:11px;padding:16px;margin-top:24px}}
</style>
</head>
<body>
<div class="header">
<h1>IfeSec Mission Control — Helix Health Portfolio</h1>
<p>AtlasPay + Helix Health + Meridian Bank | Live data from CISO Assistant API | Auto-refresh every 5 minutes</p>
<p style="margin-top:8px;font-size:11px;color:var(--crimson);">Last refreshed: {now} | Helix folder ID: {helix_folder_id or 'NOT FOUND'}</p>
</div>
<div class="grid">
{cards_html}
</div>
<div class="footer">
IfeSec Hermes Cron Generator | hermes kanban list --board portfolio-expansion | CISO Assistant v3.18.3 @ https://localhost:8443
</div>
</body></html>
"""
    OUT.write_text(html)
    print(f"Dashboard written: {OUT} (Helix folder={helix_folder_id})")
    for k, v in counts.items():
        print(f"  {k}: {v}")


if __name__ == "__main__":
    main()