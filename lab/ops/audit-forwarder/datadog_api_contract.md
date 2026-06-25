# Datadog Logs API v2 Contract

+## Endpoint

+```
POST https://http-intake.logs.datadoghq.com/api/v2/logs
```

+For EU region: `https://http-intake.logs.datadoghq.eu/api/v2/logs`

+## Authentication

+Single header, no OAuth flow:

+```
DD-API-KEY: <datadog_api_key>
```

+The API key is a 32-character hex string. Store in environment variable `DD_API_KEY` or AWS Secrets Manager. Rotate quarterly per Helix policy.

+## Request Format

+**Content-Type:** `application/json`

+**Body:** NDJSON (one JSON object per line). Datadog accepts both NDJSON and JSON array, but NDJSON is preferred for streaming.

+### Log Entry Schema

+Each line is a JSON object with Datadog reserved attributes plus custom fields:

+```json
{
  "ddsource": "ciso-assistant",
  "service": "ciso-assistant",
  "hostname": "helix-grc-01",
  "ddtags": "audit,helix,hipaa,policy.change",
  "message": "appliedcontrol.update by ijeziermf@gmail.com",
  "timestamp": "2026-06-24T20:38:56.004228Z",
  "event_type": "appliedcontrol.update",
  "actor": {
    "id": "ec85b14448e64df7abc6be14f40f7240",
    "email": "ijeziermf@gmail.com"
  },
  "source": {
    "ip": "192.168.65.1",
    "service": "ciso-assistant"
  },
  "target": {
    "resource": "appliedcontrol/e887e38d-05ab-42be-9b78-258684510c56",
    "action": "update"
  },
  "perimeter": "internal-infra",
  "severity": "info",
  "correlation_id": "e86be110-ed21-4724-b2d3-7544773c1c0b"
}
```

+### Reserved Datadog Fields

+| Field | Type | Description |
|-------|------|-------------|
| `ddsource` | string | Logical source of the log (e.g., "ciso-assistant") |
| `service` | string | Service name for grouping in Datadog |
| `hostname` | string | Host that generated the log |
| `ddtags` | string | Comma-separated tags for filtering |
| `message` | string | Human-readable summary (required by Datadog) |
| `timestamp` | string | ISO 8601 timestamp (auto-parsed by Datadog) |

+### Custom Fields

+All other fields (event_type, actor, source, target, perimeter, severity, correlation_id) are indexed as custom facets in Datadog and can be searched/filterered in Log Explorer.

+## Response

+**Success:** HTTP 202 Accepted (async ingestion)

+**Error responses:**
- 400: Bad request (malformed JSON)
# Datadog Logs API v2 Contract for Helix Audit Log Forwarding

+**Document Date:** 2026-06-24
**API Version:** Datadog Logs API v2
**Compliance Basis:** HIPAA Security Rule 45 CFR 164.312(b) - Audit Controls
For EU customers: `https://http-intake.logs.datadoghq.eu/api/v2/logs`
| Header | Value | Notes |
|--------|-------|-------|
| `DD-API-KEY` | Datadog API key | Stored in AWS Secrets Manager, rotated quarterly |
| `Content-Type` | `application/json` | Required |
**No BAA token or OAuth flow.** The API key is the sole authentication mechanism. It must have the `logs_write` scope.
## Request Body
NDJSON format (newline-delimited JSON). One log entry per line. Batch up to 50 entries per request for efficiency.
### Log Entry Schema (Datadog Envelope)
Each line is a JSON object with Datadog standard attributes plus custom Helix fields:
  "hostname": "helix-prod-01",
  "ddtags": "audit,helix,hipaa",
  "perimeter": "internal-infra",
  "severity": "info",
### Datadog Standard Fields
