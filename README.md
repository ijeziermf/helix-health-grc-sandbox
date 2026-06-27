# Helix Health HIPAA + SOC 2 GRC Engagement

A portfolio case study demonstrating the work of a vCISO embedded in a HealthTech SaaS company preparing for HIPAA Security Rule compliance, SOC 2 Type 2 observation, and HITRUST CSF certification. This repository contains the artifacts that OCR auditors, HITRUST assessors, SOC 2 audit firms, Series C investors, and BAA-covered providers would see. All content is for portfolio demonstration; the persona and supporting data are synthetic.

This is **not** a SOC 2 case study with a healthcare template bolted on. The deliverables are specific to the healthcare environment: OCR-defensible HIPAA artifacts, BAA inventory, breach notification playbook, ROPA, dual-framework cross-walk, and an operational artifact (audit log forwarder code) that ships.

---

## At a Glance

| Dimension | Value |
|---|---|
| Engagement duration | 5 hours focused (front-loaded assessment + deliverable production) |
| Client persona | 200-employee HealthTech SaaS handling 2.4M patient records |
| Frameworks in scope | HIPAA Security Rule + SOC 2 TSC 2022 + HITRUST CSF v11 (target Q4 2026 cert) + HDS v2.0 (pre-EU expansion) |
| HIPAA mapping source | NIST SP 800-66 Rev 2 (HITRUST CSF v11 not in CISO Assistant catalog) |
| Perimeters scoped | 3 (BAA-Scope PHI Processing, Provider Portal, Internal Infrastructure) |
| Risk scenarios assessed | 12 (HH-R-01 through HH-R-12) |
| BAA-covered vendors | 10 (4 Tier 1 Critical, 4 Tier 2 Important, 2 Tier 3 Deferrable) |
| Active policies | 12 (incl. BAA Policy, Breach Notification, HIPAA Security Policies) |
| BAA renewals within 60 days | 3 (Auth0, Sumo Logic, Google Workspace) |
| Risk register residual profile | 0 Very High, 0 High, 7 Moderate, 5 Low |
| Open POA&M items | 7 (all High priority) |
| ROPA entries | 15 (PHI processing activities documented) |
| SOC 2 Type 2 observation | 6 months in (Jan-Jun 2026, observation period ends Dec 2026) |
| Final deliverable count | 4 stakeholder PDFs + 7 source markdowns + 1 production-grade ops artifact (audit log forwarder) |
| Frameworks cross-walked | 4 (HIPAA + SOC 2 + HITRUST CSF + HDS v2.0) |

---

## The Engagement

### Client Profile

Helix Health is a 200-employee HealthTech SaaS serving 37 provider organizations and 4 payer partners. The platform exchanges clinical data via HL7 FHIR R4 between provider EHR systems (Epic, Cerner, Athena) and payer ingestion endpoints. All 37 provider relationships and 4 payer relationships are governed by Business Associate Agreements (BAAs).

Series B closed Q4 2025 ($48M raised). Series C in progress. SOC 2 Type 1 issued 2025-08 (no exceptions). SOC 2 Type 2 observation window started 2026-01-01. HITRUST CSF v11 self-assessment complete Q1 2026, certification targeted Q4 2026.

### Scope

- **Frameworks in scope:** HIPAA Security Rule (per §164.302-§164.318), SOC 2 Trust Services Criteria 2022, HITRUST CSF v11 (roadmap), HDS v2.0 (pre-EU expansion)
- **HIPAA mapping source:** NIST SP 800-66 Rev 2 (HITRUST CSF v11 not available in CISO Assistant v3.18.3 catalog)
- **Out of scope:** PCI DSS (no cardholder data; payments via Stripe)
- **Adjacent work:** GDPR Article 30 ROPA (best practice for HIPAA, required if EU data subjects are added)

### Why This Work Matters

For a HealthTech CISO, HIPAA readiness is patient safety and regulatory survival, not paperwork. The HIPAA Security Rule is enforced by HHS Office for Civil Rights (OCR) with civil monetary penalties ranging from $137 to $2,067,813 per violation. OCR audits are document-driven: the agency requests the Risk Analysis, the BAA inventory, the breach notification playbook, and the ROPA. If those documents are missing or incomplete, OCR escalates.

This engagement produced those documents. The artifacts are OCR-defensible per the OCR Audit Protocol. They are also useful for HITRUST assessors, SOC 2 audit firms, and Series C investors, but their primary purpose is to be ready when OCR asks.

---

## Why This is Different from a SOC 2 Case Study

The AtlasPay portfolio (`ijeziermf/atlaspay-grc-sandbox`) demonstrates FinTech SOC 2 readiness with executive briefing, risk register, control matrix, and audit walkthrough. Those artifacts do not work for healthcare. Helix needs:

| SOC 2 (FinTech) | HIPAA (Healthcare) |
|---|---|
| SOC 2 audit firm is the auditor | OCR is the regulator (federal, not contracted) |
| Auditor wants evidence of control operation | OCR wants OCR Audit Protocol documents (Risk Analysis, BAA inventory, breach playbook) |
| Vendor risk + SOC 2 collection | Vendor risk + BAA execution (legally required per §164.504(e)) |
| 72-hour GDPR + contract notification | HIPAA 60-day rule + state overlays (FL 30d, NY 30d, CA 15 business days) |
| Board briefing on payment risk | Board briefing on patient safety + clinical workflow + regulatory exposure |
| Maturity snapshot is the sales asset | HIPAA Risk Analysis is the OCR audit artifact |
| Single-framework (SOC 2) | Multi-framework (HIPAA + SOC 2 + HITRUST + HDS) |
| Audit log forwarding is best practice | Audit log forwarding is a HIPAA §164.312(b) required control |
| Documentation is the deliverable | Documentation + operational artifacts (code) are the deliverables |

Healthcare vCISO work is structurally different from FinTech vCISO work. This repository shows that difference.

---

## Risk Register Summary

The full HIPAA Risk Analysis is in `deliverables/hipaa-risk-analysis.pdf` (9 pages). The summary:

| Risk ID | Scenario | Inherent | Residual | HIPAA Safeguard | Board-Relevant |
|---|---|---|---|---|---|
| HH-R-01 | Ransomware encryption of PHI processing pipeline | 10 High | 4 Moderate | §164.308(a)(7) Contingency Plan | No |
| HH-R-02 | BAA-covered vendor breach exposing PHI | 15 High | 4 Moderate | §164.308(b)(1) Business Associate Contracts | Yes |
| HH-R-03 | Insider threat - privileged access misuse | 12 High | 4 Moderate | §164.308(a)(3) Workforce Security | No |
| HH-R-04 | Provider EHR connector compromise (supply chain) | 12 High | **9 Moderate** | §164.308(b)(1) Business Associate Contracts | Yes |
| HH-R-05 | HIPAA breach notification failure (60-day rule) | 10 High | 4 Moderate | §164.404 Notification to Individuals | Yes |
| HH-R-06 | AWS region failure (us-east-1 outage) | 6 Moderate | 4 Moderate | §164.308(a)(7) Contingency Plan | No |
| HH-R-07 | Auth0 misconfiguration exposing patient portal | 8 Moderate | 4 Moderate | §164.312(a)(1) Access Control | No |
| HH-R-08 | Inadequate BAAs with downstream vendors | 12 High | 4 Moderate | §164.308(b)(1) + §164.502(e) | Yes |
| HH-R-09 | Audit log tampering or loss | 4 Moderate | 1 Low | §164.312(b) Audit Controls | No |
| HH-R-10 | Phishing of clinical staff credentials | 9 Moderate | 4 Moderate | §164.308(a)(5) Security Awareness | No |
| HH-R-11 | Insecure direct object reference in FHIR API | 8 Moderate | 4 Moderate | §164.312(a)(1) + §164.312(e) | No |
| HH-R-12 | Key compromise (KMS, code signing) | 10 High | 4 Moderate | §164.312(a)(2)(iv) Encryption | No |

**Aggregate residual distribution:** 0 Very High, 0 High, 7 Moderate, 5 Low. All High inherent risks drop to Moderate residual. **HH-R-04 stays at residual Moderate** (NOT Low)  -  this is the honest-call discipline. Provider EHR connectors are themselves BAs (Epic, Cerner, Athena); Helix cannot eliminate the supply-chain risk, only manage it.

**4 of 12 risks are board-relevant** (HH-R-02, HH-R-04, HH-R-05, HH-R-08). These are surfaced in the board briefing.

---

## BAA Inventory Snapshot

10 BAA-covered vendors, classified by criticality:

| Vendor | Tier | PHI Touches | BAA Status | SOC 2 Type 2 | Review Cadence |
|---|---|---|---|---|---|
| Amazon Web Services | 1 Critical | All categories | Executed | On file | Quarterly |
| Datadog | 1 Critical | App logs | Executed | On file | Quarterly |
| Auth0 (Okta CIC) | 1 Critical | Auth metadata | Executed | On file | Quarterly |
| Sumo Logic | 1 Critical | Audit logs | Executed | On file | Quarterly |
| Cloudflare | 2 Important | TLS traffic | Executed | On file | Quarterly |
| Google Workspace | 2 Important | Email/docs | Executed | On file | Quarterly |
| GitHub Enterprise | 2 Important | Source code | Executed | On file | Quarterly |
| Stripe | 2 Important | Payment metadata | Executed | On file | Quarterly |
| PagerDuty | 3 Deferrable | Alerting metadata | Executed | On file | Annual |
| Vanta | 3 Deferrable | Compliance evidence | Executed | On file | Annual |

**3 BAAs require immediate renewal** (within 60 days): Google Workspace (55 days), Auth0 (76 days), Sumo Logic (76 days). The full inventory with 13-element adequacy checklist is in `deliverables/baa-inventory.pdf`.

**Critical data hygiene gap:** CISO Assistant shows 10 vendors with BAA coverage but **0 contracts loaded.** This is the kind of finding an OCR auditor would surface during an investigation. It is documented in the BAA Inventory and tracked as POA&M-06.

---

## Clinical Safety Implications (The Healthcare-Specific Dimension)

Healthcare environments have a risk dimension that does not exist in FinTech or banking: **patient safety**. Security events can delay clinical decisions, produce incorrect clinical decisions, or lose the audit trail needed for medico-legal documentation.

| Risk | Clinical Safety Implication |
|---|---|
| HH-R-01 Ransomware | PHI inaccessibility during ransomware delays clinical decisions. Provider staff may operate without patient history for 4-24 hours. |
| HH-R-04 EHR Connector Compromise | Incorrect or stale data between Helix and provider EHR could lead to wrong clinical decisions. |
| HH-R-09 Audit log tampering | Loss of audit trail means providers cannot demonstrate what data was reviewed for which patient. Medico-legal risk. |

**Clinical workflow disruption from security controls** is also a concern. Security controls can introduce friction in clinical workflows:

- MFA enforcement adds ~5 seconds per login - mitigated by session extension (15 min idle, 8 hr max)
- Background check requirements delay onboarding 3-7 days - mitigated by pre-offer background check
- Quarterly access attestation burdens provider IT teams - planned self-service portal Q4 2026

The Board + Clinical-Leadership briefing addresses these dimensions explicitly. This is not a generic SOC 2 board briefing.

---

## Multi-Framework Cross-Walk

Helix operates in a multi-framework environment. The cross-walk identifies every Helix control and the framework requirements each satisfies:

| Helix Control | HIPAA | SOC 2 | HITRUST CSF | HDS v2.0 |
|---|---|---|---|---|
| Auth0 + MFA enforcement | §164.312(a)(1), §164.312(d) | CC6.1, CC6.2 | 01.b, 01.c, 01.y | HDS-P-01 |
| Audit log forwarder (out-of-band) | §164.312(b) | CC7.2, CC7.3 | 09.aa, 09.ab | HDS-P-04 |
| BAA Policy + standard BAA template | §164.308(b)(1), §164.504(e) | CC9.2 | 05.i, 05.j, 09.e | HDS-P-06 |
| TLS 1.3 + AWS KMS HSM keys | §164.312(e)(2)(ii) | CC6.7 | 06.g, 06.h | HDS-P-05 |
| Breach Notification Playbook (60-day rule) | §164.404, §164.408, §164.410 | CC7.4 | 11.b, 11.e, 11.f | HDS-P-07 |

The full 15-domain cross-walk is in `deliverables/source-data/cross-walk-2026-06-27.md`. The cross-walk identifies single-control-multiple-framework satisfaction - one control (e.g., audit logging) satisfies requirements across all 4 frameworks. This is the foundation of efficient multi-framework compliance.

**Critical gap:** HITRUST CSF v11 is NOT in the CISO Assistant v3.18.3 catalog. The cross-walk references HITRUST requirements, but Helix cannot formally certify HITRUST until either the catalog adds HITRUST CSF v11 or Helix uses MyCSF (HITRUST Alliance's submission platform) for HITRUST-specific tracking.

---

## Operational Artifact: Audit Log Forwarder

AtlasPay's deliverable was documentation. Helix's deliverable includes **production-grade code** that ships.

`ops/audit-forwarder/` contains a working audit log forwarder:

- **`helix_audit_forwarder.py`** (128 lines) - Polls CISO Assistant's `django-auditlog` table with WAL-safe reads, forwards to configurable SIEM sinks (file, Datadog, Splunk, Elasticsearch)
- **`com.helix.audit-forwarder.plist`** - launchd daemon for auto-restart on crash
- **`datadog_api_contract.md`** - Full HTTP contract for Datadog Logs API v2
- **`trigger_control_change.py`** - Test script that emits an audit event for end-to-end verification
- **`README.md`** - Installation, configuration, verification

This artifact satisfies HIPAA §164.312(b) Audit Controls by forwarding audit logs out-of-band to Datadog and Sumo Logic within seconds. **HH-R-09 (Audit log tampering) drops to residual Low** specifically because of this forwarder - tampering requires breaking two systems simultaneously.

This is a real operational deliverable, not a placeholder. A SOC 2 Type 2 auditor or HITRUST assessor can verify the forwarder is installed and producing events. This is the kind of artifact that distinguishes a senior vCISO from a junior compliance officer.

---

## Process and Methodology

### Phase 1: Baseline (Helix Phase 1, 2026-06-24)

Established the Helix folder in CISO Assistant, ingested the persona data (12 risk scenarios, 12 policies, 10 vendors, 3 perimeters, 1 risk assessment, 5 validation flows), loaded HIPAA Security Rule framework (mapped via NIST SP-800-66 rev 2), SOC 2 TSC 2022, HDS v2.0, and supporting frameworks. Discovered that HITRUST CSF v11 is not in the v3.18.3 catalog - mapped HIPAA via NIST SP-800-66 rev 2 as fallback.

Phase 1 produced the Phase 1 ingestion report and the initial persona ingestion artifacts. The persona is the foundation; everything else builds on it.

### Phase 2: Healthcare-Specific Deliverable Production

This engagement (2026-06-27) produced the healthcare-specific deliverables that OCR auditors and HITRUST assessors look for:

- **HIPAA Risk Analysis** - OCR-defensible per §164.308(a)(1)(ii)(A)
- **BAA Inventory + Adequacy Assessment** - §164.504(e) satisfactory assurances
- **Breach Notification Playbook** - 60-day HIPAA rule operationalized
- **ROPA Summary** - 15 PHI processing activities documented
- **Multi-Framework Cross-Walk** - HIPAA + SOC 2 + HITRUST + HDS
- **Board + Clinical-Leadership Briefing** - patient safety + clinical workflow + regulatory exposure
- **Audit Log Forwarder** - production-grade code in `ops/audit-forwarder/`

### Risk Scoring Methodology

**Threat Likelihood (1-5):** Very Low to Very High, mapped to healthcare sector incident frequency
**Impact (1-5):** Negligible to Catastrophic, mapped to HIPAA breach notification thresholds (500-individual media notice threshold)
**Risk = Likelihood x Impact.** Range 1-25.

| Score | Level |
|---|---|
| 1-3 | Low |
| 4-9 | Moderate |
| 10-15 | High |
| 16-25 | Very High |

### HIPAA Safeguard Mapping Discipline

Every risk scenario is mapped to its governing HIPAA Security Rule safeguard:

- **Administrative Safeguards** (§164.308) - policies, training, workforce security, contingency planning
- **Physical Safeguards** (§164.310) - facility access, workstation use, device controls
- **Technical Safeguards** (§164.312) - access control, audit controls, integrity, transmission security

This mapping is what OCR auditors look for in a Risk Analysis. A risk register without safeguard mapping is incomplete.

---

## Key Findings (Substantive Healthcare Observations)

### 1. Healthcare risk register residual floors are different from FinTech

In AtlasPay's FinTech SOC 2 register, R-04 (Third-Party SaaS Breach) sits at residual High and stays there. In Helix's HIPAA register, **HH-R-04 (Provider EHR Connector Compromise) sits at residual Moderate and stays there** - NOT Low, despite all the controls. The reasoning is structurally the same: third-party vendors (Epic, Cerner, Athena) are themselves BAs with their own security postures. Helix can verify SOC 2 reports, monitor security ratings, and pin configurations, but cannot eliminate the supply-chain risk. The honest position is residual Moderate.

### 2. BAA inventory is not the same as vendor inventory

In FinTech/SOC 2, vendor risk management is a contractual question. In HIPAA, BAA execution is a **legal requirement before any PHI disclosure** (§164.502(e)). The 13-element adequacy checklist (per §164.504(e)) is the standard. Every BAA must satisfy all 13 elements. This is a different evaluation than "do we have a signed contract."

### 3. Breach notification is the hardest HIPAA control to operationalize

The 60-day rule (§164.404-§164.414) requires:
- Decision under time pressure (60-day clock starts at discovery)
- Multi-stakeholder notification (individuals, OCR, media, state AGs)
- 4-factor risk assessment documented per §164.402(2)
- Coordination with Business Associates and Covered Entities
- State-specific overlays (FL 30 days, NY 30 days, CA 15 business days)

The Breach Notification Playbook operationalizes all of this with decision trees, notification templates, and a quarterly drill cadence. The playbook is the operational artifact AtlasPay doesn't have.

### 4. Clinical safety is the primary risk dimension in healthcare

In FinTech, the primary risk dimension is financial loss and customer trust. In healthcare, the primary risk dimension is patient safety. Security events can delay clinical decisions, produce incorrect decisions, or lose the medico-legal audit trail. The Board + Clinical-Leadership briefing addresses clinical safety implications explicitly - this is not in AtlasPay's board briefing.

### 5. Multi-framework compliance is the default in healthcare

FinTech SOC 2 engagements are usually single-framework. Healthcare engagements are always multi-framework: HIPAA + SOC 2 + HITRUST CSF + (sometimes) HDS or GDPR. The cross-walk document is essential infrastructure, not optional. Helix's cross-walk covers 4 frameworks across 15 domains.

### 6. HITRUST CSF v11 catalog gap is a real-world issue

The CISO Assistant v3.18.3 catalog does NOT include HITRUST CSF v11. This is a meaningful gap that affects Q4 2026 certification efficiency. The recommendation: either upgrade CISO Assistant when HITRUST CSF v11 becomes available, or use MyCSF for HITRUST-specific tracking. The cross-walk covers the gap at the control level.

### 7. Audit log forwarding is a HIPAA-required control, not a nice-to-have

§164.312(b) requires audit controls. Helix's audit log forwarder pushes logs out-of-band to Datadog + Sumo Logic within seconds. This is the operational artifact that distinguishes a HIPAA-engaged vCISO from a documentation-only vCISO. HH-R-09 (Audit log tampering) drops to residual Low because of this forwarder.

### 8. BAA renewals have hard deadlines

If a BAA expires without renewal, Helix is **prohibited from disclosing PHI to that vendor**. PHI flow must stop immediately upon expiry until renewal completes. This is operationally different from a vendor contract with a lapsed SLA. The BAA Inventory tracks renewal dates with 60-day threshold triggers.

---

## Audit Readiness Projection

| Quarter | HIPAA Readiness | Key Gates |
|---|---|---|
| Q3 2026 | 90% | EDR rollout + BAA review + breach notification drill |
| Q4 2026 | 95% | SOC 2 Type 2 observation ends + HITRUST CSF validated assessment |
| Q1 2027 | 100% | SOC 2 Type 2 report + HITRUST CSF certification issuance |

**HIPAA alone is continuous (per §164.308(a)(8) evaluation cycle).** SOC 2 Type 2 and HITRUST CSF are point-in-time certifications.

---

## Residuals to Carry Into the Next Healthcare Engagement

The following patterns came out of this engagement and should be applied to every future healthcare GRC engagement:

1. **OCR-defensibility is the primary standard.** Every HIPAA artifact must be ready for production submission to OCR. Generic compliance documentation does not survive an OCR investigation.
2. **BAA execution is a legal requirement, not a contractual nicety.** Treat every BAA-covered vendor as a separate legal entity with §164.504(e) satisfactory assurance documentation.
3. **Honest residual risk reporting.** HH-R-04 stays at Moderate because third-party EHR systems are themselves BAs. Don't deflate residuals to make the register look cleaner.
4. **Clinical safety is the primary risk dimension.** Address patient safety implications explicitly in board briefings and risk documentation.
5. **Multi-framework cross-walk is infrastructure, not optional.** Build it once, reuse for HITRUST CSF + HDS + future frameworks.
6. **Operational artifacts (code) ship alongside documentation.** Audit log forwarder is a HIPAA §164.312(b) required control. Ship the code, not just the documentation.
7. **Breach notification playbook is drilled quarterly.** §164.404-§164.414 are operationally complex. Tabletop drill is the only way to verify the playbook works.
8. **State overlays must be in the breach playbook.** FL 30 days, NY 30 days, CA 15 business days. The federal HIPAA 60-day rule is the floor; states can be stricter.
9. **HITRUST CSF v11 catalog gap affects certification efficiency.** Track HITRUST separately in MyCSF until CISO Assistant catalog adds it.
10. **BAA renewals have hard deadlines.** If BAA expires, PHI disclosure to that vendor is prohibited. Track renewals with 60-day threshold triggers.
11. **Audit log forwarder drops tampering risk to residual Low.** Out-of-band forwarding to two independent sinks (Datadog + Sumo Logic) means tampering requires breaking two systems.
12. **The HIPAA Risk Analysis is the OCR-specific document.** It's not a generic risk register. It maps to §164.308(a)(1)(ii)(A) explicitly with safeguard mappings.

---

## Deliverables

### Stakeholder-Facing PDFs (5 files, v3 brand-compliant)

| Deliverable | Purpose | Pages | Audience |
|---|---|---|---|
| [HIPAA Risk Analysis](deliverables/hipaa-risk-analysis.pdf) | OCR-defensible per §164.308(a)(1)(ii)(A), 12 risk heatmap | 9 | OCR auditors, Compliance Committee |
| [BAA Inventory + Adequacy Assessment](deliverables/baa-inventory.pdf) | §164.504(e) satisfactory assurances, BAA chain diagram | 8 | Legal, TPRM, OCR auditors |
| [Breach Notification Playbook](deliverables/breach-notification-playbook.pdf) | HIPAA 60-day rule operationalized, decision flow | 11 | CISO, Legal, on-call team |
| [Multi-Framework Cross-Walk](deliverables/cross-walk.pdf) | HIPAA + SOC 2 + HITRUST + HDS coverage matrix | 9 | Compliance leadership, multi-framework assessors |
| [Board + Clinical-Leadership Briefing](deliverables/board-clinical-briefing.pdf) | Quarterly board briefing | 8 | Board, Clinical Advisory Board, CEO |

**Total:** 45 pages of OCR-defensible HIPAA documentation across 5 stakeholder-facing PDFs.

### Evidence-Quality Visuals (4 diagrams)

Generated for the v3 stakeholder-facing PDFs (no UI screenshots, no platform captures — these show the analyst's output, not the platform's UI):

| Visual | Source PDF | What it shows |
|---|---|---|
| [HIPAA 5x5 Risk Heatmap (INHERENT vs RESIDUAL)](assets/images/helix-risk-heatmap.png) | hipaa-risk-analysis.pdf, page 5 | All 12 HIPAA risks plotted side-by-side, residual all lower than inherent |
| [BAA Chain (10 vendors, 3 tiers, AWS subprocessing)](assets/images/helix-baa-chain.png) | baa-inventory.pdf, page 6 | Covered Entity + Business Associate structure per §164.504(e), 4 Critical / 4 Important / 2 Deferrable |
| [Breach Notification Flow (60-day clock + 4-factor assessment)](assets/images/helix-breach-notification-flow.png) | breach-notification-playbook.pdf, page 5 | Decision flow with 3 branches (Presumed / Mixed / Low), state overlays (FL/NY/CA) |
| [Multi-Framework Cross-Walk Matrix](assets/images/helix-cross-walk.png) | cross-walk.pdf, page 3 | 12 Helix controls × 4 frameworks (HIPAA Security Rule, SOC 2 TSC 2022, HITRUST CSF v11, HDS v2.0) |

### Source Markdowns (7 files)

The engagement record from start to finish, in `deliverables/source-data/`:

| File | What It Documents |
|---|---|
| `state-2026-06-27.md` | Live state snapshot of CISO Assistant (12 risks, 12 policies, 10 vendors, etc.) |
| `hipaa-risk-analysis-2026-06-27.md` | HIPAA Risk Analysis source markdown |
| `baa-inventory-2026-06-27.md` | BAA Inventory source markdown |
| `breach-notification-playbook-2026-06-27.md` | Breach Notification Playbook source markdown |
| `ropa-summary-2026-06-27.md` | 15 PHI processing activities ROPA |
| `cross-walk-2026-06-27.md` | Multi-framework cross-walk (HIPAA + SOC 2 + HITRUST + HDS) — 12 controls x 4 frameworks |
| `board-clinical-briefing-2026-06-27.md` | Board + Clinical-Leadership briefing source |

### Operational Artifact (1 directory, 5 files)

`ops/audit-forwarder/` - Production-grade audit log forwarder:

| File | Purpose |
|---|---|
| `helix_audit_forwarder.py` | Main daemon - polls CISO Assistant, forwards to SIEM sinks |
| `com.helix.audit-forwarder.plist` | launchd daemon for auto-restart on crash |
| `datadog_api_contract.md` | Full HTTP contract for Datadog Logs API v2 |
| `trigger_control_change.py` | Test script that emits audit events |
| `README.md` | Installation, configuration, verification |

### Reference Material

`lab/source-data/helix_persona_spec.json` - Helix persona specification (input data).

---

## Related Portfolio Work

Other engagements using the same Solo vCISO operating model, available as separate repositories:

- **AtlasPay GRC Sandbox** - FinTech SOC 2 readiness for a payment processor persona
- **Meridian Bank GRC Sandbox** - FFIEC CAT + GLBA Safeguards + SOX ITGC posture for a community bank persona

---

## License

This portfolio demonstration work is for educational and hiring-manager review purposes. Organizations may adapt the methodology for internal use. See `LICENSE` for full terms.