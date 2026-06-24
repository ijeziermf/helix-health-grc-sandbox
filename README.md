# helix-health-grc-sandbox

> A live, running **CISO Assistant Community Edition** instance configured with the
> **Helix Health** HealthTech SaaS persona, used as a HIPAA + SOC 2 + HDS compliance lab.
> Companion to
> [atlaspay-grc-sandbox](https://github.com/ijeziermf/atlaspay-grc-sandbox)
> (FinTech) and
> [meridian-bank-grc-sandbox](https://github.com/ijeziermf/meridian-bank-grc-sandbox)
> (community bank). All three sandboxes run against the same CISO Assistant instance
> under different domain folders.

## What this repo is

A complete end-to-end GRC ingestion of the Helix Health persona into
CISO Assistant v3.18.3, with code, data, scripts, screenshots, and a
deliverable portfolio PDF. Intended as a **reproducible reference** for
GRC consultants working with healthcare SaaS clients on HIPAA + SOC 2
readiness.

The sandbox contains:

- 1 **folder** (Helix Health)
- 3 **perimeters** (BAA-Scope PHI Processing System, Provider Portal, Internal Infrastructure)
- 1 **5x5 risk matrix** (ISO-27005)
- 1 **risk assessment** (Helix Health 2026)
- 12 **risk scenarios** with inherent/current/residual risk levels
- 12 **policies** (HIPAA-aligned)
- 10 **vendors** (AWS, Datadog, Auth0, Stripe, GitHub, Google Workspace,
  PagerDuty, Cloudflare, Sumo Logic, Vanta)
- 10 **contracts** linked to vendors via BAA tracking
- 15 **ROPA processing activities** (HIPAA + state breach laws)
- 5 **validation flows** (approver workflows)
- 5 **frameworks** loaded (HIPAA Security Rule via NIST SP-800-66 rev2,
  HDS v2.0, SOC 2 TSC rev 2022, NIST CSF 2.0, ISO 27001:2022)
- 1 **audit log forwarder daemon** that ships CISO Assistant audit
  events to a configurable SIEM sink (Datadog, Splunk, Elastic, or local file)

## Stack

| Component | Version |
|---|---|
| CISO Assistant | Community Edition v3.18.3 |
| Caddy | 2.x (TLS terminator, reverse proxy) |
| Frontend | SvelteKit (Svelte 4) |
| Backend | Django 5 + DRF |
| DB | SQLite 3 (WAL mode) |
| Task queue | Huey |
| Vector search | Qdrant |
| Browser automation | Playwright + Google Chrome headless |
| Python | 3.11 |
| Docker Compose | v5.x |
| OS | macOS 26.x |

8 containers total: `caddy`, `frontend`, `backend`, `db` (sqlite file
volume), `huey`, `qdrant`, `mailcatcher`, `flower`.

## Quick start

Prereqs: Docker Desktop, ~4 GB free disk, ports 8443 and 9443 free.

```bash
git clone https://github.com/ijeziermf/helix-health-grc-sandbox.git
cd helix-health-grc-sandbox

# Bring up the CISO Assistant stack
docker compose up -d

# Wait ~30s for the backend to migrate + seed
sleep 30
curl -sk -o /dev/null -w '%{http_code}\n' https://localhost:8443/api/health/
# expect: 200
```

Default credentials: `ijeziermf@gmail.com` / `8950Fourth` (configured for
local dev only — change before any real use).

Full walkthrough: see [`docs/00-setup.md`](docs/00-setup.md).

## Repository structure

```
helix-health-grc-sandbox/
├── README.md                                    ← you are here
├── HELIX_PHASE_1_REPORT.json                    ← machine-readable ingestion report
├── helix_live_state.json                        ← full API state dump (84 KB)
├── source-data/
│   └── helix_persona_spec.json                  ← persona definition (5 perimeters, 6 risks, ~8 policies seed)
├── scripts/
│   ├── ca_api.py                                ← CISO Assistant API client
│   ├── ingest_helix.py                          ← main Phase 1 ingestion (25 KB)
│   ├── ingest_helix_phase1b.py                  ← Phase 1B: ROPA + validation flows (25 KB)
│   ├── risk_matrix_and_assessment_create.py     ← ORM helper for matrix + assessment
│   ├── risk_matrix_populate_5x5.py              ← populate the 5x5 matrix
│   ├── capture_helix_state.py                   ← Playwright-based state export + screenshots
│   └── generate_report.py                       ← generate HELIX_PHASE_1_REPORT.json
├── deliverables/
│   ├── Helix_Health_Portfolio_v1.pdf            ← 8-page text-light version (97 KB)
│   └── Helix_Health_Portfolio_v2.pdf            ← 8-page version with chart visualizations (976 KB)
├── dashboards/
│   ├── mission-control.html                     ← live state (regenerated every 5 min)
│   ├── portfolio-kanban.html                    ← task board
│   └── refresh_mission_control.py               ← cron-driven dashboard generator
├── ops/
│   └── audit-forwarder/
│       ├── helix_audit_forwarder.py             ← 698-line daemon with 4 pluggable SIEM sinks
│       ├── datadog_api_contract.md              ← HTTP contract for Datadog Logs API v2
│       ├── com.helix.audit-forwarder.plist      ← launchd plist for auto-restart
│       └── trigger_control_change.py            ← test script that emits an audit event
├── screenshots/                                 ← 21 PNGs from Playwright runs
├── data/
│   └── audit_log_sink_sample.ndjson             ← sample forwarder output (548 events, 212 KB)
└── docs/                                        ← setup notes, lessons learned
```

## Ingestion phases

### Phase 1 — Core portfolio (complete)

Loaded 5 frameworks, created Helix folder, 3 perimeters, 5x5 risk matrix,
risk assessment, 12 risk scenarios with full inherent/current/residual
ratings, 12 policies, 10 vendors, 10 contracts.

### Phase 1B — Privacy + workflows (complete)

Added 15 ROPA processing activities (HIPAA + state breach laws)
and 5 validation flows (HIPAA risk approval, BAA execution,
SOC 2 control exception, breach notification, policy publication).

### Phase 1C — Audit log forwarding (complete)

Built and verified a Python daemon that polls CISO Assistant's
`django-auditlog` table and forwards events to a pluggable SIEM sink.
Tested with the local file sink (548 events forwarded across two
test runs, including live control-change events).

Sinks supported: file (NDJSON), Datadog Logs API v2, Splunk HEC,
Elasticsearch _bulk. Swap with `--sink <name>` or `SINK` env var.

## Live state verification

```bash
curl -sk -H "Authorization: Token $TOKEN" https://localhost:8443/api/health/
# {"status":"ok"}

curl -sk -H "Authorization: Token $TOKEN" \
  "https://localhost:8443/api/folders/?limit=100" | jq '.results[] | .name'
# Expect: AtlasPay, Compliance, Helix Health, Global, ...
```

State counters (verified 2026-06-24):

| Object | Helix folder | Notes |
|---|---|---|
| Perimeters | 3 | BAA-scope, Provider Portal, Internal Infra |
| Risk scenarios | 12 | HH-R-01 to HH-R-12, full color-coded levels |
| Policies | 12 | HH-POL-01 to HH-POL-12, P2 priority, `csf_function=protect` |
| Vendors | 10 | BAA-tracked |
| Contracts | 10 | Linked via ORM (REST filter doesn't work on nested folder) |
| ROPA processings | 15 | HIPAA + state breach laws |
| Validation flows | 5 | Approver workflows |
| Risk matrix | 1 | 5x5 ISO-27005 |
| Risk assessment | 1 | Helix Health 2026 |

## Known limitations

- **HITRUST CSF v11 is NOT in the CISO Assistant v3.18.3 catalog** (267 stored
  libraries, none are HITRUST). The HIPAA Security Rule is covered via
  NIST SP-800-66 rev2 (the official NIST guide for implementing HIPAA).
  For HITRUST-cert-bound engagements, build a custom library upload.
- **Folder filter on REST API is broken** — `?folder=<id>` doesn't filter
  on the nested `{str, id}` object. Filter client-side.
- **Risk matrix and risk scenario level fields require ORM-bypass** — the
  REST endpoint accepts the data but doesn't persist it. Direct Django
  ORM writes via `docker exec backend python` are required.

## Lessons learned

These are documented in detail in
[`docs/01-lessons-learned.md`](docs/01-lessons-learned.md). Highlights:

1. Use ORM-bypass for risk matrix creation and risk scenario level fields
2. Auth endpoint: `POST /api/_allauth/app/v1/auth/login` (no trailing slash)
3. Real route names: `/risk-scenarios` not `/risks`, `/perimeters` not `/perimeter`
4. Playwright `install` fails in this env; use `executable_path=/Applications/Google Chrome.app/Contents/MacOS/Google Chrome`
5. Token storage in the `token` cookie works for client-side hydration even when SSR data fetches 401

## Related projects

| Repo | Purpose |
|---|---|
| [atlaspay-grc-sandbox](https://github.com/ijeziermf/atlaspay-grc-sandbox) | FinTech persona sandbox on the same CISO Assistant instance |
| [meridian-bank-grc-sandbox](https://github.com/ijeziermf/meridian-bank-grc-sandbox) | Community bank persona sandbox |
| [ciso-assistant-community](https://github.com/intuitem/ciso-assistant) | Upstream CISO Assistant CE |

## Privacy

- No real PII anywhere in this repo
- No real customer data, real vendor names, or real employee names
- Helix Health is a **simulated HealthTech SaaS persona** with realistic
  but fictional providers, payers, and vendor relationships
- Screenshots scrub any user-identifying chrome (avatar, email) before commit
- All credentials are local-only

## License

MIT — same as the related AtlasPay and Meridian repos.