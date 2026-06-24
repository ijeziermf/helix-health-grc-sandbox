#!/usr/bin/env python3
"""
Helix Health Phase 1B - ROPA + Validation Flows + Audit Log Config.

Creates:
  1. 15 ROPA (Records of Processing Activities) entries via POST /api/privacy/processings/
  2. 5 validation flows via POST /api/validation-flows/
  3. Audit log forwarding config doc (markdown) in Obsidian vault

Idempotent: checks for existing entries by ref_id before creating.
"""
from __future__ import annotations
import json
import re
import ssl
import subprocess
import urllib.error
import urllib.request
import urllib.parse
from pathlib import Path
from datetime import datetime, timezone, timedelta

# --- Config ---
ENV_PATH = Path("/Users/ifeanyi/Documents/IfeSec/Tools/ciso-assistant-community/cli/.mcp.env")
PROJECT_DIR = Path("/Users/ifeanyi/Documents/IfeSec/Projects/helix-health-grc-sandbox")
VAULT_DOC_PATH = Path("/Users/ifeanyi/Documents/Obsidian Vault/20-Decisions/2026-06-24-Helix-Audit-Log-Forwarding.md")

API_BASE = "https://localhost:8443/api"
SSL_CTX = ssl._create_unverified_context()
HELIX_FOLDER_ID = "c912e8a5-379a-4484-b01e-14d4102753c4"

# Perimeter IDs from Phase 1
PERIMETER_PHI = "ca576150-e74d-4941-87c4-81dd1f0f6677"
PERIMETER_PORTAL = "a4ded43f-2302-4f52-a1cd-6a28054fd998"
PERIMETER_INTERNAL = "663e69ad-cb23-4e01-8b83-afecbec2697b"


def _get_token():
    """Source TOKEN from .mcp.env via bash subprocess (avoids shell sanitization)."""
    out = subprocess.run(
        ["bash", "-c", f"source {ENV_PATH} && echo $TOKEN"],
        capture_output=True, text=True, timeout=10
    )
    token = out.stdout.strip()
    if not token:
        raise RuntimeError("TOKEN not found in .mcp.env")
    return token


_TOKEN = None


def _token():
    global _TOKEN
    if _TOKEN is None:
        _TOKEN = _get_token()
    return _TOKEN


def api(method, path, body=None):
    """REST call with Token auth. Returns (status_code, parsed_json)."""
    url = API_BASE + path
    data = None
    headers = {"Authorization": f"Token {_token()}", "Accept": "application/json"}
    if body is not None:
        data = json.dumps(body).encode()
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        resp = urllib.request.urlopen(req, context=SSL_CTX, timeout=30)
        raw = resp.read()
        return resp.status, json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        raw = e.read()
        try:
            return e.code, json.loads(raw)
        except Exception:
            return e.code, {"raw": raw.decode(errors="replace")}


def api_all(path, page_size=200):
    """Paginated list."""
    qs = f"limit={page_size}"
    _, data = api("GET", f"{path}?{qs}")
    results = data.get("results", []) if isinstance(data, dict) else []
    next_url = data.get("next") if isinstance(data, dict) else None
    while next_url:
        next_endpoint = re.sub(r"^/api/", "", next_url)
        next_endpoint = next_endpoint.split("?")[0]
        _, next_data = api("GET", next_endpoint)
        results.extend(next_data.get("results", []))
        next_url = next_data.get("next")
    return results


def find_by_ref_id(path, ref_id):
    """Find an object by ref_id field."""
    results = api_all(path)
    for r in results:
        if r.get("ref_id") == ref_id:
            return r
    return None


def find_all_by_ref_id_prefix(path, prefix):
    """Find all objects whose ref_id starts with the given prefix."""
    results = api_all(path)
    return [r for r in results if r.get("ref_id", "").startswith(prefix)]


def get_user_id():
    """Get the first (only) user ID from the API."""
    _, data = api("GET", "/users/?limit=10")
    results = data.get("results", [])
    if results:
        return results[0]["id"]
    raise RuntimeError("No users found in CISO Assistant")


# --- 15 ROPA entries ---
ROPA_ENTRIES = [
    {
        "name": "Provider-payer PHI data exchange (HL7 FHIR R4)",
        "ref_id": "HH-ROPA-01",
        "description": "Core processing: receives PHI from 37 provider EHR integrations (Epic, Cerner, Athena), normalizes to HL7 FHIR R4, transmits to 4 payer partners under BAA. Lawful basis: HIPAA TPO. Data subjects: patients of provider organizations. Sensitive data: yes (PHI).",
        "dpia_required": True,
        "dpia_reference": "HH-DPIA-2026-01",
        "has_sensitive_personal_data": True,
        "perimeters": [PERIMETER_PHI],
    },
    {
        "name": "Payer claim adjudication data delivery",
        "ref_id": "HH-ROPA-02",
        "description": "Delivers normalized claim data to payer partners for adjudication. Includes CPT/ICD-10 codes, member IDs, and provider NPIs. Transmitted via SFTP with PGP encryption. BAA executed with all 4 payers. Sensitive data: yes (PHI).",
        "dpia_required": True,
        "dpia_reference": "HH-DPIA-2026-02",
        "has_sensitive_personal_data": True,
        "perimeters": [PERIMETER_PHI],
    },
    {
        "name": "Provider EHR connector synchronization",
        "ref_id": "HH-ROPA-03",
        "description": "Scheduled synchronization jobs pulling PHI from provider EHR systems via HL7 v2 and FHIR APIs. Connectors run in helix-prod-phi AWS account. Includes patient demographics, encounter data, clinical observations. Sensitive data: yes (PHI).",
        "dpia_required": True,
        "dpia_reference": "HH-DPIA-2026-03",
        "has_sensitive_personal_data": True,
        "perimeters": [PERIMETER_PHI],
    },
    {
        "name": "Provider portal user registration and MFA enrollment",
        "ref_id": "HH-ROPA-04",
        "description": "Provider organization staff register for portal access. Auth0 (Okta CIC) manages identity with MFA enforcement. Collects name, email, provider organization, role. BAA executed with Auth0. Data subjects: provider staff. Sensitive data: no.",
        "dpia_required": False,
        "has_sensitive_personal_data": False,
        "perimeters": [PERIMETER_PORTAL],
    },
    {
        "name": "Provider portal session management and access logs",
        "ref_id": "HH-ROPA-05",
        "description": "Active session tracking, timeout enforcement (15 min idle), per-session audit logging of all PHI views. Logs forwarded to Datadog. Data subjects: provider staff and patients. Sensitive data: yes (audit logs contain PHI access records).",
        "dpia_required": True,
        "dpia_reference": "HH-DPIA-2026-04",
        "has_sensitive_personal_data": True,
        "perimeters": [PERIMETER_PORTAL],
    },
    {
        "name": "Provider portal role-based access control administration",
        "ref_id": "HH-ROPA-06",
        "description": "Admin management of RBAC roles (clinical viewer, clinical editor, payer liaison, admin). Includes role assignment audit trail. Access changes require CISO approval via validation flow. Sensitive data: no.",
        "dpia_required": False,
        "has_sensitive_personal_data": False,
        "perimeters": [PERIMETER_PORTAL],
    },
    {
        "name": "PHI access audit log collection and forwarding to Datadog",
        "ref_id": "HH-ROPA-07",
        "description": "All PHI access events collected from application layer and forwarded to Datadog HIPAA-eligible SIEM in us-east-1. NDJSON format. ~12M events/day. Retention: 2190 days (6 years per HIPAA 164.312(b)). Sensitive data: yes.",
        "dpia_required": True,
        "dpia_reference": "HH-DPIA-2026-05",
        "has_sensitive_personal_data": True,
        "perimeters": [PERIMETER_PHI],
    },
    {
        "name": "Audit log integrity monitoring (tamper detection)",
        "ref_id": "HH-ROPA-08",
        "description": "Continuous monitoring of audit log streams for tamper attempts, gaps, or unauthorized modifications. Alerts via PagerDuty. Datadog log immutability lock enabled. Sensitive data: yes (security event metadata).",
        "dpia_required": False,
        "has_sensitive_personal_data": True,
        "perimeters": [PERIMETER_PHI],
    },
    {
        "name": "Customer support ticket intake (PHI-containing tickets)",
        "ref_id": "HH-ROPA-09",
        "description": "Support tickets submitted by provider staff that may contain PHI (screenshots, data exports, error messages with patient data). Tickets routed via Zendesk with BAA. Auto-redaction pipeline for PHI in ticket text. Sensitive data: yes.",
        "dpia_required": True,
        "dpia_reference": "HH-DPIA-2026-06",
        "has_sensitive_personal_data": True,
        "perimeters": [PERIMETER_PORTAL],
    },
    {
        "name": "Customer support ticket resolution and evidence retention",
        "ref_id": "HH-ROPA-10",
        "description": "Resolved tickets and associated evidence (logs, screenshots, communications) retained for 6 years per HIPAA documentation requirements. Access restricted to support engineering and compliance. Sensitive data: yes.",
        "dpia_required": False,
        "has_sensitive_personal_data": True,
        "perimeters": [PERIMETER_PORTAL],
    },
    {
        "name": "Sales pipeline CRM (no PHI processed)",
        "ref_id": "HH-ROPA-11",
        "description": "Salesforce CRM managing prospective provider organization and payer contacts. Contains business contact information only. No PHI is processed, stored, or transmitted. BAA not required for Salesforce. Sensitive data: no.",
        "dpia_required": False,
        "has_sensitive_personal_data": False,
        "perimeters": [PERIMETER_INTERNAL],
    },
    {
        "name": "Employee HR records (onboarding, payroll, benefits)",
        "ref_id": "HH-ROPA-12",
        "description": "HRIS (BambooHR) processing of employee personal data: SSN, payroll, benefits enrollment, performance reviews. No PHI from customers processed in HR systems. Data subjects: Helix Health employees. Sensitive data: yes (SSN, health plan elections).",
        "dpia_required": False,
        "has_sensitive_personal_data": True,
        "perimeters": [PERIMETER_INTERNAL],
    },
    {
        "name": "Employee background check processing",
        "ref_id": "HH-ROPA-13",
        "description": "Pre-employment background checks via Checkr. Processes criminal history, education verification, employment verification. Data retained 7 years per EEOC guidance. Sensitive data: yes (criminal history).",
        "dpia_required": False,
        "has_sensitive_personal_data": True,
        "perimeters": [PERIMETER_INTERNAL],
    },
    {
        "name": "BAA-covered vendor onboarding and risk assessment",
        "ref_id": "HH-ROPA-14",
        "description": "Processing of vendor security documentation (SOC 2 reports, HITRUST certifications, penetration test results) during BAA onboarding. 8 critical BAA vendors, 4 critical non-BAA vendors. Sensitive data: no.",
        "dpia_required": False,
        "has_sensitive_personal_data": False,
        "perimeters": [PERIMETER_INTERNAL],
    },
    {
        "name": "Vendor BAA execution and renewal tracking",
        "ref_id": "HH-ROPA-15",
        "description": "Tracking of BAA execution dates, renewal cycles, and vendor breach notification obligations. 10 vendors with signed BAAs. BAA renewals tracked 90 days before expiry. Sensitive data: no.",
        "dpia_required": False,
        "has_sensitive_personal_data": False,
        "perimeters": [PERIMETER_INTERNAL],
    },
]


# --- 5 Validation Flows ---
VALIDATION_FLOWS = [
    {
        "name": "HIPAA risk assessment approval",
        "ref_id": "HH-VF-01",
        "description": "Annual HIPAA Security Rule risk assessment requires CISO, Privacy Officer, and CEO approval before publication. SLA: 72 hours from submission.",
        "sla_hours": 72,
    },
    {
        "name": "BAA execution (new vendor)",
        "ref_id": "HH-VF-02",
        "description": "New Business Associate Agreement for vendor with PHI access requires Privacy Officer, Legal, and CISO approval. SLA: 120 hours (5 business days).",
        "sla_hours": 120,
    },
    {
        "name": "SOC 2 control exception",
        "ref_id": "HH-VF-03",
        "description": "SOC 2 Type 2 control exception requires CISO, VP Engineering, and Auditor liaison approval. SLA: 168 hours (7 business days). Exception must include compensating control documentation.",
        "sla_hours": 168,
    },
    {
        "name": "Breach notification (HIPAA 60-day rule)",
        "ref_id": "HH-VF-04",
        "description": "Suspected HIPAA breach requiring notification within 60 days. Requires Privacy Officer, CEO, Legal, and CISO approval. SLA: 24 hours from detection. Triggers incident response runbook.",
        "sla_hours": 24,
    },
    {
        "name": "Policy publication",
        "ref_id": "HH-VF-05",
        "description": "New or updated policy publication requires CISO and Department Head approval. SLA: 48 hours. Includes 30-day staff review period before effective date.",
        "sla_hours": 48,
    },
]


AUDIT_LOG_DOC = """# Helix Health Audit Log Forwarding Configuration

**Decision Date:** 2026-06-24
**Decision Owner:** CISO (Helix Health)
**Compliance Basis:** HIPAA Security Rule 45 CFR 164.312(b) - Audit Controls
**Review Cycle:** Annual (next review: 2027-06-24)

## Purpose

Define the audit log forwarding configuration for Helix Health's BAA-scope PHI processing system. All audit events from the PHI processing pipeline, provider portal, and internal infrastructure are forwarded to a centralized SIEM for security monitoring, breach detection, and compliance evidence collection.

## Target SIEM

| Field | Value |
|---|---|
| **SIEM Platform** | Datadog (HIPAA-eligible deployment) |
| **Region** | us-east-1 (HIPAA-eligible AWS region) |
| **BAA Status** | BAA executed with Datadog (critical_no_baa tier, no PHI access) |
| **Intake Method** | Datadog Agent (HTTP log forwarding) |
| **Forwarding Protocol** | HTTPS/TLS 1.2+ |
| **Authentication** | Datadog API key (stored in AWS Secrets Manager, rotated quarterly) |

## Event Types

| Event Type | Source Systems | Volume Estimate | Priority |
|---|---|---|---|
| `auth.login` | Auth0, Okta SSO, AWS IAM | ~500K/day | P2 |
| `auth.failed` | Auth0, Okta SSO, AWS IAM | ~50K/day | P1 (alert on spike) |
| `phi.access` | Provider portal, FHIR API | ~8M/day | P2 |
| `phi.export` | Provider portal, FHIR API | ~20K/day | P1 (alert on bulk) |
| `policy.change` | CISO Assistant, Okta admin | ~100/day | P1 (alert on all) |
| `audit_log.tamper_attempt` | Datadog Agent, log shipper | ~0/day expected | P0 (alert on any) |

## Log Format

**Format:** NDJSON (Newline-Delimited JSON)

Per CISO Assistant `structured-logging` documentation, all events are serialized as one JSON object per line. Example:

```json
{"timestamp":"2026-06-24T17:15:32.123Z","event_type":"phi.access","actor":{"id":"user_abc","role":"clinical_viewer"},"target":{"resource":"fhir/Patient/12345","action":"read"},"source":{"ip":"10.0.1.42","service":"provider-portal"},"perimeter":"phi-processing","severity":"info"}
{"timestamp":"2026-06-24T17:15:33.456Z","event_type":"auth.failed","actor":{"id":"unknown","email":"admin@hospital.org"},"source":{"ip":"203.0.113.50","service":"auth0"},"perimeter":"provider-portal","severity":"warn"}
```

**Schema fields:**
- `timestamp` - ISO 8601 UTC, millisecond precision
- `event_type` - One of the 6 event types listed above
- `actor` - {id, role, email (if available)}
- `target` - {resource, action} for PHI access events
- `source` - {ip, service}
- `perimeter` - One of: `phi-processing`, `provider-portal`, `internal-infra`
- `severity` - One of: `debug`, `info`, `warn`, `error`, `critical`

## Retention

| Parameter | Value | Basis |
|---|---|---|
| **Hot retention (Datadog)** | 90 days | Operational investigation window |
| **Cold retention (S3 Glacier)** | 2,190 days (6 years) | HIPAA 164.316(b)(2) - documentation retention |
| **Archive format** | Compressed NDJSON (gzip) | Storage efficiency |
| **Archive location** | s3://helix-audit-log-archive/us-east-1/ | HIPAA-eligible AWS region |
| **Archive encryption** | AES-256 (SSE-KMS) | HIPAA 164.312(a)(2)(iv) - encryption |
| **Immutability** | S3 Object Lock (COMPLIANCE mode) | Prevents tampering, audit integrity |

## Alerting Rules

| Rule | Condition | Action |
|---|---|---|
| `auth.failed_spike` | > 20 failed logins from same IP in 5 min | PagerDuty P1, auto-block IP via Cloudflare |
| `phi.export_bulk` | > 500 patient records exported by single user in 1 hour | PagerDuty P1, notify CISO + Privacy Officer |
| `policy.change` | Any policy.change event | PagerDuty P2, notify CISO |
| `audit_log.tamper` | Any tamper_attempt event | PagerDuty P0, notify CISO + CEO, trigger IR runbook |
| `log_gap` | No logs received from a service for > 15 min | PagerDuty P1, verify Datadog Agent health |

## Compliance Mapping

| HIPAA Control | How This Config Satisfies It |
|---|---|
| 164.312(b) - Audit Controls | All PHI access logged and forwarded to centralized SIEM |
| 164.312(c)(1) - Integrity | S3 Object Lock prevents log tampering; Datadog immutability lock |
| 164.316(b)(2) - Retention | 6-year retention (2,190 days) in S3 Glacier with Object Lock |
| 164.312(a)(2)(iv) - Encryption | AES-256 at rest (SSE-KMS), TLS 1.2+ in transit |
| 164.308(a)(3) - Workforce security | Audit logs capture actor identity for all events |

## Failover

- **Primary:** Datadog Agent direct forwarding to Datadog us-east-1
- **Secondary:** Sumo Logic (BAA not signed, no PHI in logs - metadata only) for operational dashboards
- **Archive:** S3 Glacier with Object Lock (independent of Datadog availability)

If Datadog is unavailable, logs buffer locally for 24 hours (Datadog Agent disk buffer) before failing over to S3 direct upload via log shipper sidecar.

## Review History

| Date | Reviewer | Changes |
|---|---|---|
| 2026-06-24 | CISO (initial) | Initial configuration established |
"""


def create_ropa_entries():
    """Create 15 ROPA entries via POST /api/privacy/processings/."""
    print("\n=== STEP 1: Create 15 ROPA entries ===")
    created = 0
    skipped = 0
    failed = []

    for entry in ROPA_ENTRIES:
        existing = find_by_ref_id("/privacy/processings", entry["ref_id"])
        if existing:
            print(f"  ... {entry['ref_id']} already exists (skip)")
            skipped += 1
            continue

        payload = {
            "name": entry["name"],
            "ref_id": entry["ref_id"],
            "description": entry["description"],
            "folder": HELIX_FOLDER_ID,
            "status": "privacy_approved",
            "dpia_required": entry.get("dpia_required", False),
            "has_sensitive_personal_data": entry.get("has_sensitive_personal_data", False),
            "perimeters": entry.get("perimeters", []),
        }
        if entry.get("dpia_reference"):
            payload["dpia_reference"] = entry["dpia_reference"]

        status, body = api("POST", "/privacy/processings/", payload)
        if 200 <= status < 300:
            created += 1
            print(f"  OK  {entry['ref_id']}: {entry['name'][:60]}")
        else:
            failed.append((entry["ref_id"], status, str(body)[:300]))
            print(f"  FAIL {entry['ref_id']}: HTTP {status} {str(body)[:300]}")

    print(f"\n  ROPA: created={created}, skipped={skipped}, failed={len(failed)}")
    return created, skipped, failed


def create_validation_flows(user_id):
    """Create 5 validation flows via POST /api/validation-flows/."""
    print("\n=== STEP 2: Create 5 validation flows ===")
    created = 0
    skipped = 0
    failed = []

    now = datetime.now(timezone.utc)

    for vf in VALIDATION_FLOWS:
        existing = find_by_ref_id("/validation-flows", vf["ref_id"])
        if existing:
            print(f"  ... {vf['ref_id']} already exists (skip)")
            skipped += 1
            continue

        deadline = now + timedelta(hours=vf["sla_hours"])

        payload = {
            "ref_id": vf["ref_id"],
            "folder": HELIX_FOLDER_ID,
            "approver": user_id,
            "status": "submitted",
            "request_notes": vf["description"],
            "validation_deadline": deadline.strftime("%Y-%m-%d"),
            "is_published": True,
        }

        status, body = api("POST", "/validation-flows/", payload)
        if 200 <= status < 300:
            created += 1
            print(f"  OK  {vf['ref_id']}: {vf['name'][:60]}")
        else:
            failed.append((vf["ref_id"], status, str(body)[:300]))
            print(f"  FAIL {vf['ref_id']}: HTTP {status} {str(body)[:300]}")

    print(f"\n  Validation flows: created={created}, skipped={skipped}, failed={len(failed)}")
    return created, skipped, failed


def create_audit_log_doc():
    """Write the audit log forwarding config doc to Obsidian vault."""
    print("\n=== STEP 3: Write audit log forwarding config doc ===")
    VAULT_DOC_PATH.parent.mkdir(parents=True, exist_ok=True)
    VAULT_DOC_PATH.write_text(AUDIT_LOG_DOC)
    print(f"  OK  Written to: {VAULT_DOC_PATH}")
    return True


def verify():
    """Verify final state."""
    print("\n=== VERIFICATION ===")

    _, ropa_data = api("GET", f"/privacy/processings/?folder={HELIX_FOLDER_ID}&limit=1")
    ropa_count = ropa_data.get("count", 0) if isinstance(ropa_data, dict) else 0
    print(f"  ROPA (processings) count for Helix folder: {ropa_count}")

    ropa_all = find_all_by_ref_id_prefix("/privacy/processings", "HH-ROPA-")
    print(f"  ROPA entries with HH-ROPA- ref_id: {len(ropa_all)}")

    _, vf_data = api("GET", f"/validation-flows/?folder={HELIX_FOLDER_ID}&limit=1")
    vf_count = vf_data.get("count", 0) if isinstance(vf_data, dict) else 0
    print(f"  Validation flows count for Helix folder: {vf_count}")

    doc_exists = VAULT_DOC_PATH.exists()
    doc_size = VAULT_DOC_PATH.stat().st_size if doc_exists else 0
    print(f"  Audit log doc exists: {doc_exists} (size: {doc_size} bytes)")

    return {
        "ropa_count": ropa_count,
        "ropa_ref_ids": len(ropa_all),
        "validation_flows_count": vf_count,
        "audit_log_doc_exists": doc_exists,
        "audit_log_doc_size": doc_size,
        "audit_log_doc_path": str(VAULT_DOC_PATH),
    }


def update_report(verification):
    """Update HELIX_PHASE_1_REPORT.json with Phase 1B counts."""
    print("\n=== UPDATE REPORT ===")
    report_path = PROJECT_DIR / "HELIX_PHASE_1_REPORT.json"
    with open(report_path, "r") as f:
        report = json.load(f)

    if "phase_1b" not in report:
        report["phase_1b"] = {}

    report["phase_1b"] = {
        "completed_at": datetime.now(timezone.utc).isoformat(),
        "ropa_entries": {
            "count": verification["ropa_count"],
            "target": 15,
            "status": "complete" if verification["ropa_count"] >= 15 else "incomplete",
        },
        "validation_flows": {
            "count": verification["validation_flows_count"],
            "target": 5,
            "status": "complete" if verification["validation_flows_count"] >= 5 else "incomplete",
        },
        "audit_log_config": {
            "doc_path": verification["audit_log_doc_path"],
            "doc_exists": verification["audit_log_doc_exists"],
            "doc_size_bytes": verification["audit_log_doc_size"],
        },
    }

    report["counts"]["ropa_entries"] = verification["ropa_count"]
    report["counts"]["validation_flows"] = verification["validation_flows_count"]

    new_next_steps = [
        "Upload custom HITRUST CSF v11 JSON if required (not in v3.18.3 catalog)",
        "Configure audit log forwarding cron to Datadog (config doc written, implementation pending)",
        "Begin Meridian Bank (third persona) - blocked on AtlasPay residuals fix",
    ]
    report["next_steps"] = new_next_steps

    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
    print(f"  OK  Updated: {report_path}")
    return report_path


def main():
    print("=" * 70)
    print("HELIX HEALTH PHASE 1B - ROPA + Validation Flows + Audit Log Config")
    print("=" * 70)

    status, _ = api("GET", "/health/")
    print(f"\nSmoke test: /api/health/ -> HTTP {status}")

    user_id = get_user_id()
    print(f"User ID: {user_id}")

    ropa_created, ropa_skipped, ropa_failed = create_ropa_entries()
    vf_created, vf_skipped, vf_failed = create_validation_flows(user_id)
    doc_written = create_audit_log_doc()

    verification = verify()
    report_path = update_report(verification)

    print("\n" + "=" * 70)
    print("PHASE 1B COMPLETE")
    print("=" * 70)
    print(f"  ROPA entries:      {verification['ropa_count']} / 15 (created={ropa_created}, skipped={ropa_skipped}, failed={len(ropa_failed)})")
    print(f"  Validation flows:  {verification['validation_flows_count']} / 5 (created={vf_created}, skipped={vf_skipped}, failed={len(vf_failed)})")
    print(f"  Audit log doc:     {verification['audit_log_doc_exists']} ({verification['audit_log_doc_size']} bytes)")
    print(f"  Report updated:    {report_path}")

    if ropa_failed:
        print(f"\n  ROPA FAILURES: {ropa_failed}")
    if vf_failed:
        print(f"\n  VF FAILURES: {vf_failed}")

    return verification


if __name__ == "__main__":
    main()