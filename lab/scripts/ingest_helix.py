#!/usr/bin/env python3
"""
Helix Health Phase 1 — full CISO Assistant ingestion.

Loads HIPAA Security Rule + HITRUST CSF v11 frameworks, creates the Helix
folder + 3 perimeters + risk matrix + risk assessment, then 12 risks, 12
policies, 10 entities + contracts, ROPA, validation flows.

Idempotent where possible (existence checks before create). ORM-bypass for
risk matrices and risk assessments per the known v3.18.3 server bugs.

Run via the venv python directly (NOT `uv run` per skill pitfalls):
    /Users/ifeanyi/.hermes/hermes-agent/venv/bin/python3 ingest_helix.py
"""
from __future__ import annotations
import json
import os
import ssl
import subprocess
import sys
import urllib.request
import urllib.error
from pathlib import Path

# --- Config (loaded from .mcp.env via subprocess to bypass shell sanitization) ---
ENV_PATH = Path("/Users/ifeanyi/Documents/IfeSec/Tools/ciso-assistant-community/cli/.mcp.env")
PERSONA_SPEC_PATH = Path("/Users/ifeanyi/Documents/IfeSec/Projects/helix-health-grc-sandbox/source-data/helix_persona_spec.json")
ROOT_PROJECT_DIR = Path("/Users/ifeanyi/Documents/IfeSec/Projects/helix-health-grc-sandbox")

API_BASE = "https://localhost:8443/api"
SSL_CTX = ssl._create_unverified_context()  # self-signed cert, dev only


def load_token():
    """Source TOKEN/API_URL from .mcp.env via bash subprocess (avoids shell sanitization)."""
    out = subprocess.run(
        ["bash", "-c", f"source {ENV_PATH} && echo $TOKEN"],
        capture_output=True, text=True, timeout=10
    )
    token = out.stdout.strip()
    if not token:
        raise RuntimeError("TOKEN not found in .mcp.env")
    return token


TOKEN = load_token()


def api(method, path, body=None, expect_json=True):
    """REST call with Token auth. Returns (status_code, parsed_json_or_text)."""
    url = API_BASE + path
    data = None
    headers = {"Authorization": f"Token {TOKEN}", "Accept": "application/json"}
    if body is not None:
        data = json.dumps(body).encode()
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        resp = urllib.request.urlopen(req, context=SSL_CTX, timeout=30)
        raw = resp.read()
        return resp.status, json.loads(raw) if expect_json and raw else raw
    except urllib.error.HTTPError as e:
        raw = e.read()
        try:
            return e.code, json.loads(raw)
        except Exception:
            return e.code, raw.decode(errors="replace")


def api_count(path):
    """Count results via /api/<path>/?limit=1, reading the count field."""
    _, data = api("GET", f"/{path}/?limit=1")
    if isinstance(data, dict):
        return data.get("count", len(data.get("results", [])))
    return len(data or [])


def api_find_by(path, **filters):
    """Find first object matching filters (e.g., name=...)."""
    qs = "&".join(f"{k}={urllib.parse.quote(str(v))}" for k, v in filters.items())
    _, data = api("GET", f"/{path}/?{qs}")
    if isinstance(data, dict):
        results = data.get("results", [])
    else:
        results = data or []
    if not results:
        return None
    # If filter was on name, find exact match (API may return substring matches)
    if "name" in filters:
        for r in results:
            if r.get("name") == filters["name"]:
                return r
    return results[0]


def api_create_or_skip(path, payload, name_field="name"):
    """Create if not exists. Returns (created, object)."""
    existing = api_find_by(path, **{name_field: payload.get(name_field, "")})
    if existing:
        return False, existing
    status, body = api("POST", f"/{path}/", payload)
    if 200 <= status < 300:
        return True, body
    raise RuntimeError(f"POST {path} returned {status}: {body}")


# --- Step 1: Load HIPAA Security Rule + HITRUST CSF v11 frameworks ---
def step_load_frameworks():
    print("\n=== STEP 1: Load HIPAA Security Rule + HITRUST CSF v11 ===")
    libraries = [
        ("HIPAA Security Rule", "urn:intuitem:risk:library:hipaa-security-rule"),
        ("HITRUST CSF v11", "urn:intuitem:risk:library:hitrust-csf-v11"),
        ("SOC 2 TSC 2017", "urn:intuitem:risk:library:soc2-tsc-2017"),
        ("NIST CSF 2.0", "urn:intuitem:risk:library:nist-csf-2.0"),
    ]
    loaded_before = api_count("loaded-libraries")
    print(f"  Loaded libraries BEFORE: {loaded_before}")
    for name, urn in libraries:
        existing = api_find_by("loaded-libraries", name=name)
        if existing:
            print(f"  ✓ {name} already loaded (id={existing.get('id', '?')[:8]})")
            continue
        # The skill says: path is /import/ not /load/
        import_path = f"/stored-libraries/{urn}/import/"
        status, body = api("POST", import_path, {})
        if 200 <= status < 300:
            print(f"  ✓ Loaded {name} (status={status})")
        else:
            print(f"  ✗ Failed to load {name}: HTTP {status} body={str(body)[:200]}")
    loaded_after = api_count("loaded-libraries")
    print(f"  Loaded libraries AFTER: {loaded_after} (delta={loaded_after - loaded_before})")
    return loaded_after


# --- Step 2: Create Helix folder ---
def step_create_folder():
    print("\n=== STEP 2: Create Helix folder ===")
    # Folders use /api/folders/ POST with {name, parent_folder, content_type}
    # Top-level Domain folder has parent_folder=null and content_type="DOMAIN"
    existing = api_find_by("folders", name="Helix Health")
    if existing:
        print(f"  ✓ Helix Health folder exists (id={existing.get('id')})")
        return existing
    payload = {
        "name": "Helix Health",
        "parent_folder": None,
        "content_type": "DOMAIN",
        "description": "Helix Health, Inc. — Healthcare SaaS, BAA-covered PHI processing. 200 employees, 37 provider customers, 4 payer partners. HQ Boston MA.",
    }
    created, folder = api_create_or_skip("folders", payload)
    if created:
        print(f"  ✓ Created Helix Health folder (id={folder.get('id')})")
    return folder


# --- Step 3: Create 3 perimeters ---
def step_create_perimeters(folder):
    print("\n=== STEP 3: Create 3 perimeters ===")
    perimeters_spec = [
        {
            "name": "Helix BAA-Scope PHI Processing System",
            "description": "Core provider-payer data exchange platform. Receives PHI from provider EHR integrations, normalizes to HL7 FHIR R4, transmits to payer partners under BAA. AWS account: helix-prod-phi.",
            "scope_in": ["PHI processing pipeline", "HL7 FHIR R4 API", "Provider EHR connectors (Epic, Cerner, Athena)", "Payer-side ingestion endpoints", "Audit log forwarding"],
            "scope_out": ["Corporate IT (separate perimeter)", "Internal HR systems (no PHI)", "Public marketing site"],
        },
        {
            "name": "Helix Provider Portal",
            "description": "Web application accessed by provider organization staff. BAA-covered because users view PHI. Built on React + Node.js, runs in helix-prod-app AWS account.",
            "scope_in": ["Web app frontend", "API gateway", "Authentication (Auth0 with MFA)", "Session management", "Provider-side audit logs"],
            "scope_out": ["Internal admin tools (separate perimeter)"],
        },
        {
            "name": "Helix Internal Infrastructure",
            "description": "Corporate IT, internal admin tools, HR systems, corporate AWS account. Not BAA-covered but supports the BAA scope indirectly.",
            "scope_in": ["Okta SSO", "Google Workspace", "Slack", "GitHub Enterprise", "Corporate AWS account (helix-corp)"],
            "scope_out": ["Production PHI processing (separate perimeter)"],
        },
    ]
    folder_id = folder["id"]
    results = []
    for spec in perimeters_spec:
        existing = api_find_by("perimeters", name=spec["name"])
        if existing:
            print(f"  ✓ Perimeter exists: {spec['name']}")
            results.append(existing)
            continue
        payload = {
            "name": spec["name"],
            "folder": folder_id,
            "description": spec["description"],
            "scope_in": spec["scope_in"],
            "scope_out": spec["scope_out"],
        }
        status, body = api("POST", "/perimeters/", payload)
        if 200 <= status < 300:
            print(f"  ✓ Created perimeter: {spec['name']} (id={body.get('id')[:8]})")
            results.append(body)
        else:
            print(f"  ✗ Failed perimeter {spec['name']}: HTTP {status} {str(body)[:200]}")
    perim_count = api_count("perimeters")
    print(f"  Total perimeters after: {perim_count}")
    return results


# --- Step 4: Create risk matrix + risk assessment via ORM (REST BROKEN for these) ---
def step_create_matrix_and_assessment(folder):
    print("\n=== STEP 4: Create risk matrix + assessment (ORM-bypass required) ===")

    # 5x5 ISO-27005 standard matrix
    matrix_json = {
        "type": "standard",
        "probability": [
            {"abbreviation": "1", "name": "Rare", "description": "Highly unlikely, almost never"},
            {"abbreviation": "2", "name": "Unlikely", "description": "Possible but unusual"},
            {"abbreviation": "3", "name": "Possible", "description": "Could occur occasionally"},
            {"abbreviation": "4", "name": "Likely", "description": "Will probably occur"},
            {"abbreviation": "5", "name": "Almost Certain", "description": "Expected to occur"},
        ],
        "impact": [
            {"abbreviation": "1", "name": "Insignificant", "description": "Minimal impact"},
            {"abbreviation": "2", "name": "Minor", "description": "Limited impact"},
            {"abbreviation": "3", "name": "Moderate", "description": "Notable impact"},
            {"abbreviation": "4", "name": "Major", "description": "Significant impact"},
            {"abbreviation": "5", "name": "Severe", "description": "Catastrophic impact"},
        ],
        "risk": [
            {"abbreviation": "VL", "name": "Very Low", "description": "Accept risk", "hexcolor": "#10b981"},
            {"abbreviation": "L", "name": "Low", "description": "Monitor and manage", "hexcolor": "#84cc16"},
            {"abbreviation": "M", "name": "Medium", "description": "Mitigate actively", "hexcolor": "#eab308"},
            {"abbreviation": "H", "name": "High", "description": "Mitigate urgently", "hexcolor": "#f97316"},
            {"abbreviation": "VH", "name": "Very High", "description": "Avoid or transfer", "hexcolor": "#dc2626"},
        ],
        "grid": [
            [{"color": "#10b981", "abbreviation": "VL"}, {"color": "#10b981", "abbreviation": "VL"}, {"color": "#84cc16", "abbreviation": "L"}, {"color": "#eab308", "abbreviation": "M"}, {"color": "#f97316", "abbreviation": "H"}],
            [{"color": "#10b981", "abbreviation": "VL"}, {"color": "#84cc16", "abbreviation": "L"}, {"color": "#eab308", "abbreviation": "M"}, {"color": "#f97316", "abbreviation": "H"}, {"color": "#dc2626", "abbreviation": "VH"}],
            [{"color": "#84cc16", "abbreviation": "L"}, {"color": "#eab308", "abbreviation": "M"}, {"color": "#eab308", "abbreviation": "M"}, {"color": "#f97316", "abbreviation": "H"}, {"color": "#dc2626", "abbreviation": "VH"}],
            [{"color": "#eab308", "abbreviation": "M"}, {"color": "#f97316", "abbreviation": "H"}, {"color": "#f97316", "abbreviation": "H"}, {"color": "#dc2626", "abbreviation": "VH"}, {"color": "#dc2626", "abbreviation": "VH"}],
            [{"color": "#f97316", "abbreviation": "H"}, {"color": "#dc2626", "abbreviation": "VH"}, {"color": "#dc2626", "abbreviation": "VH"}, {"color": "#dc2626", "abbreviation": "VH"}, {"color": "#dc2626", "abbreviation": "VH"}],
        ],
    }

    # Build ORM script
    python_code = f'''
import django, os, sys, json
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ciso_assistant.settings")
django.setup()
from core.models import RiskMatrix, RiskAssessment, Folder

# Check for existing matrix
existing_matrix = RiskMatrix.objects.filter(name="Helix 5x5 ISO-27005").first()
if existing_matrix:
    print("MATRIX_EXISTS:" + str(existing_matrix.id))
else:
    matrix = RiskMatrix.objects.create(
        name="Helix 5x5 ISO-27005",
        description="Standard 5x5 likelihood-impact matrix for Helix Health risk assessment",
        json_definition={json.dumps(matrix_json)},
        urn="urn:intuitem:risk:matrix:helix-5x5-iso27005",
        provider="custom",
    )
    print("MATRIX_CREATED:" + str(matrix.id))

# Check for existing assessment
existing_ra = RiskAssessment.objects.filter(name="Helix Health Risk Assessment 2026").first()
if existing_ra:
    print("RA_EXISTS:" + str(existing_ra.id))
else:
    matrix = RiskMatrix.objects.get(name="Helix 5x5 ISO-27005")
    folder = Folder.objects.get(name="Helix Health")
    ra = RiskAssessment.objects.create(
        name="Helix Health Risk Assessment 2026",
        description="Annual HIPAA + SOC 2 risk assessment for Helix Health, 2026 observation period",
        folder=folder,
        risk_matrix=matrix,
        status="in_progress",
        version="1.0",
        eta="2026-12-31",
        risk_tolerance=3,  # moderate (integer per model probe)
        ref_id="HH-RA-2026-01",
    )
    print("RA_CREATED:" + str(ra.id))
'''

    # Pipe the python code into the backend container
    result = subprocess.run(
        ["docker", "exec", "-i", "backend", "python", "-c",
         "import sys; exec(sys.stdin.read())"],
        input=python_code,
        capture_output=True, text=True, timeout=60,
    )
    out_lines = result.stdout.strip().split("\n")
    matrix_id = None
    ra_id = None
    for line in out_lines:
        if line.startswith("MATRIX_"):
            matrix_id = line.split(":")[1]
            print(f"  ✓ Risk matrix (id={matrix_id})")
        elif line.startswith("RA_"):
            ra_id = line.split(":")[1]
            print(f"  ✓ Risk assessment (id={ra_id})")
    if result.stderr:
        for line in result.stderr.strip().split("\n")[-3:]:
            print(f"  [backend stderr] {line}")
    return {"matrix_id": matrix_id, "ra_id": ra_id}


# --- Step 5: Create 12 risk scenarios via REST ---
def step_create_risks(folder, matrix_id, ra_id):
    print("\n=== STEP 5: Create 12 risk scenarios ===")
    # AtlasPay session used inherent_level/residual_level as 1-25 integer scores
    # per the matrix definition (proba*impact). Same pattern here.
    risks = [
        # ref_id, name, inherent_score(1-25), residual_score(1-25), treatment
        ("HH-R-01", "Ransomware encryption of PHI processing pipeline", 25, 10, "mitigate"),
        ("HH-R-02", "BAA-covered vendor breach exposing PHI", 20, 9, "mitigate"),
        ("HH-R-03", "Insider threat - privileged access misuse", 16, 6, "mitigate"),
        ("HH-R-04", "Provider EHR connector compromise (supply chain)", 20, 12, "mitigate"),
        ("HH-R-05", "HIPAA breach notification failure (60-day rule)", 12, 4, "mitigate"),
        ("HH-R-06", "AWS region failure (us-east-1 outage)", 9, 6, "accept"),
        ("HH-R-07", "Auth0 misconfiguration exposing patient portal", 15, 9, "mitigate"),
        ("HH-R-08", "Inadequate BAAs with downstream vendors", 16, 8, "mitigate"),
        ("HH-R-09", "Audit log tampering or loss", 12, 4, "mitigate"),
        ("HH-R-10", "Phishing of clinical staff credentials", 12, 6, "mitigate"),
        ("HH-R-11", "Insecure direct object reference in FHIR API", 16, 8, "mitigate"),
        ("HH-R-12", "Key compromise (KMS, code signing)", 12, 6, "mitigate"),
    ]
    created_count = 0
    skipped_count = 0
    failed = []
    for ref_id, name, inherent, residual, treatment in risks:
        # Use exact ref_id match via API: get all then filter client-side
        all_data = api("GET", "/risk-scenarios/?limit=100")[1]
        existing = None
        if isinstance(all_data, dict):
            existing = next((r for r in all_data.get("results", []) if r.get("ref_id") == ref_id), None)
        if existing:
            skipped_count += 1
            print(f"  ⊙ {ref_id} exists (skip)")
            continue
        payload = {
            "name": f"{ref_id}: {name}",
            "description": f"Helix Health risk scenario. {name}. HIPAA Security Rule + HITRUST CSF v11 alignment.",
            "inherent_level": inherent,  # 1-25 score
            "residual_level": residual,
            "treatment": treatment,
            "ref_id": ref_id,
            "folder": folder["id"],
            "risk_assessment": ra_id,
        }
        status, body = api("POST", "/risk-scenarios/", payload)
        if 200 <= status < 300:
            created_count += 1
            print(f"  ✓ {ref_id}: {name[:50]}")
        else:
            failed.append((ref_id, status, str(body)[:200]))
            print(f"  ✗ {ref_id}: HTTP {status} {str(body)[:200]}")
    risk_total = api_count("risk-scenarios")
    print(f"  Created: {created_count}, Skipped: {skipped_count}, Failed: {len(failed)}, Total: {risk_total}")
    return created_count, skipped_count


# --- Step 6: Create 12 policies ---
def step_create_policies(folder):
    print("\n=== STEP 6: Create 12 policies ===")
    policies = [
        ("Information Security Policy", "policy"),
        ("HIPAA Security Policies and Procedures", "policy"),
        ("Access Control & Privileged Access Policy", "policy"),
        ("Business Associate Agreement (BAA) Policy", "policy"),
        ("Breach Notification Policy (HIPAA 60-day rule)", "policy"),
        ("Incident Response Policy", "process"),
        ("Vendor / Third-Party Risk Management Policy", "process"),
        ("Risk Management Policy", "policy"),
        ("Encryption & Key Management Policy", "technical"),
        ("Audit Logging & Monitoring Policy", "technical"),
        ("Data Backup & Recovery Policy", "technical"),
        ("Security Awareness & Acceptable Use Policy", "procedure"),
    ]
    created_count = 0
    skipped_count = 0
    for i, (name, category) in enumerate(policies):
        ref_id = f"HH-POL-{i+1:02d}"
        existing = api_find_by("policies", ref_id=ref_id)
        if existing:
            skipped_count += 1
            continue
        # Per skill pitfalls: status="active", priority=int 1-4 (P1-P4), csf_function=lowercase
        payload = {
            "name": name,
            "ref_id": ref_id,
            "description": f"{name} for Helix Health. HIPAA + SOC 2 evidence.",
            "status": "active",
            "priority": 2,  # P2
            "csf_function": "protect",  # lowercase
            "category": category,
            "folder": folder["id"],
            "expiry_date": "2027-06-24",
        }
        status, body = api("POST", "/policies/", payload)
        if 200 <= status < 300:
            created_count += 1
            print(f"  ✓ {ref_id}: {name[:50]}")
        else:
            print(f"  ✗ {ref_id} failed: HTTP {status} {str(body)[:200]}")
    policy_total = api_count("policies")
    print(f"  Created: {created_count}, Skipped: {skipped_count}, Total policies: {policy_total}")
    return created_count, skipped_count


# --- Step 7: Create 10 entities (vendors) + 10 contracts via ORM linking ---
def step_create_tprm(folder):
    print("\n=== STEP 7: Create 10 entities + 10 contracts ===")
    vendors = [
        ("Amazon Web Services", "critical_no_baa", True, False, "Hosting (us-east-1, us-west-2)"),
        ("Datadog", "critical_no_baa", True, False, "APM, log aggregation, audit log forwarding target"),
        ("Auth0 (Okta CIC)", "critical_baa", True, True, "Identity provider for provider portal"),
        ("Stripe", "low", False, False, "Payment processing (subscriptions only, no PHI)"),
        ("GitHub Enterprise", "high", False, False, "Source code hosting, CI/CD"),
        ("Google Workspace", "medium", True, False, "Email, docs (no PHI in Workspace)"),
        ("PagerDuty", "medium", False, False, "Incident alerting"),
        ("Cloudflare", "high", False, False, "WAF, DDoS protection"),
        ("Sumo Logic", "high", False, False, "Secondary log aggregation"),
        ("Vanta", "medium", True, False, "Compliance evidence collection"),
    ]

    # First create entities via REST
    entity_ids = []
    for name, tier, baa, phi, service in vendors:
        ref_id = f"HH-VEN-{name[:3].upper()}"
        existing = api_find_by("entities", name=name)
        if existing:
            print(f"  ✓ Entity exists: {name}")
            entity_ids.append((existing["id"], name, baa))
            continue
        payload = {
            "name": name,
            "ref_id": ref_id,
            "description": f"{service}. Tier: {tier}. BAA: {'Yes' if baa else 'No'}. PHI access: {'Yes' if phi else 'No'}.",
            "folder": folder["id"],
        }
        status, body = api("POST", "/entities/", payload)
        if 200 <= status < 300:
            entity_ids.append((body["id"], name, baa))
            print(f"  ✓ Created entity: {name}")
        else:
            print(f"  ✗ Failed entity {name}: HTTP {status} {str(body)[:200]}")

    # Create contracts via REST + ORM-link entity field
    print("  Creating contracts...")
    contract_ids = []
    for i, (entity_id, name, baa) in enumerate(entity_ids):
        ref_id = f"HH-CON-{i+1:02d}"
        existing = api_find_by("contracts", ref_id=ref_id)
        if existing:
            print(f"  ✓ Contract exists: {ref_id} ({name})")
            contract_ids.append(existing["id"])
            continue
        payload = {
            "name": f"MSA — {name}",
            "ref_id": ref_id,
            "description": f"Master Service Agreement with {name}. {'BAA executed.' if baa else 'No BAA — vendor does not access PHI.'}",
            "folder": folder["id"],
            "category": "msa",
        }
        status, body = api("POST", "/contracts/", payload)
        if 200 <= status < 300:
            contract_ids.append(body["id"])
            print(f"  ✓ Created contract: {ref_id}")
        else:
            print(f"  ✗ Failed contract {ref_id}: HTTP {status} {str(body)[:200]}")

    # ORM-link contracts to entities (per skill pitfall #16) - capture output via sentinel
    print("  ORM-linking contracts to entities...")
    linking_lines = []
    for contract_id, (entity_id, name, _baa) in zip(contract_ids, entity_ids):
        linking_lines.append(
            f"Contract.objects.filter(id='{contract_id}').update(entity=Entity.objects.get(id='{entity_id}'))"
        )
    python_code = f'''
import django, os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ciso_assistant.settings")
django.setup()
from tprm.models import Entity, Contract
{chr(10).join(linking_lines)}
print("LINKED:" + str(Contract.objects.exclude(entity__isnull=True).count()))
'''
    result = subprocess.run(
        ["docker", "exec", "-i", "backend", "python", "-c", "import sys; exec(sys.stdin.read())"],
        input=python_code,
        capture_output=True, text=True, timeout=60,
    )
    for line in result.stdout.strip().split("\n"):
        if line.startswith("LINKED:"):
            print(f"  ✓ Contracts linked to entities: {line.split(':')[1]}")

    return len(entity_ids), len(contract_ids)


# --- Step 8: Verification ---
def step_verify():
    print("\n=== STEP 8: Verify final state ===")
    counts = {
        "folders": api_count("folders"),
        "perimeters": api_count("perimeters"),
        "risk-scenarios": api_count("risk-scenarios"),
        "policies": api_count("policies"),
        "entities": api_count("entities"),
        "contracts": api_count("contracts"),
        "loaded-libraries": api_count("loaded-libraries"),
        "risk-assessments": api_count("risk-assessments"),
        "risk-matrices": api_count("risk-matrices"),
    }
    print("  Object counts:")
    for k, v in counts.items():
        print(f"    {k:20s}: {v}")
    return counts


# --- Main ---
def main():
    print("=" * 70)
    print("HELIX HEALTH PHASE 1 — CISO Assistant Ingestion")
    print("=" * 70)

    # Quick smoke test
    print("\nSmoke test: /api/health/")
    status, _ = api("GET", "/health/")
    print(f"  HTTP {status}")

    # Pre-state
    print("\n--- Pre-state ---")
    pre_counts = step_verify()

    # Run steps
    step_load_frameworks()
    folder = step_create_folder()

    # Step 3: Create 3 perimeters
    step_create_perimeters(folder)

    # Step 4: Create risk matrix + risk assessment via ORM
    matrix_ra = step_create_matrix_and_assessment(folder)

    # Step 5-7 only run if we have a valid risk_assessment ID
    if matrix_ra["ra_id"] and matrix_ra["matrix_id"]:
        step_create_risks(folder, matrix_ra["matrix_id"], matrix_ra["ra_id"])
    else:
        print("\n=== STEP 5: SKIPPED (no risk_assessment ID) ===")
    step_create_policies(folder)
    step_create_tprm(folder)

    # Post-state
    print("\n--- Post-state ---")
    post_counts = step_verify()

    # Save report
    report = {
        "phase": "Helix Health Phase 1",
        "completed_at": "2026-06-24",
        "pre": pre_counts,
        "post": post_counts,
        "delta": {k: post_counts[k] - pre_counts[k] for k in pre_counts},
    }
    report_path = ROOT_PROJECT_DIR / "PHASE_1_INGESTION_REPORT.json"
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
    print(f"\n✓ Report saved: {report_path}")
    print("\nNext: capture screenshots via Playwright (separate script).")


if __name__ == "__main__":
    main()