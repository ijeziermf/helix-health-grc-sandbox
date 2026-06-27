# Helix Audit Log Forwarder

A Python daemon that polls CISO Assistant's `django-auditlog` table and
forwards each new audit event to a configurable SIEM sink. Built for the
Helix Health sandbox but reusable for any CISO Assistant deployment.

## Why

CISO Assistant logs all create/update/delete operations on objects to
`django-auditlog`. For HIPAA + SOC 2 compliance, those events need to
ship to a SIEM with 6-year retention. This forwarder does that without
requiring every consultant to build custom Datadog/Splunk/Elastic
integration code per engagement.

## Sinks supported

| Sink | `--sink` value | Use case |
|---|---|---|
| Local NDJSON file | `file` | Dev, test, sandbox |
| Datadog Logs API v2 | `datadog` | Production (Datadog SIEM) |
| Splunk HEC | `splunk` | Banking, regulated industries |
| Elasticsearch _bulk | `elastic` | Self-hosted ELK |

Swapping sinks is one flag (`--sink datadog`) or env var (`SINK=datadog`).

## Quick start

### File sink (default, no credentials)

```bash
python3 helix_audit_forwarder.py \
    --sink file \
    --db-path /Users/ifeanyi/Documents/IJZ-Workspace/Tools/ciso-assistant-community/db/ciso-assistant.sqlite3 \
    --output /var/log/helix/audit.ndjson
```

### Datadog sink

```bash
export DD_API_KEY=***
export DD_SITE=datadoghq.com  # or datadoghq.eu, us3.datadoghq.com, etc.

python3 helix_audit_forwarder.py \
    --sink datadog
```

### Splunk HEC

```bash
export SPLUNK_HEC_URL=https://splunk.example.com:8088
export SPLUNK_HEC_TOKEN=***

python3 helix_audit_forwarder.py \
    --sink splunk
```

## Daemon mode

Install the launchd plist:

```bash
cp com.helix.audit-forwarder.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.helix.audit-forwarder.plist
```

The plist sets `KeepAlive=true` so the forwarder auto-restarts on crash.

## Verification

Run the trigger script to emit an audit event, then check the sink:

```bash
# Trigger a control change (logs in, PATCHes an AppliedControl)
python3 trigger_control_change.py

# Within ~3 seconds the event should land in your sink
tail -n 1 /var/log/helix/audit.ndjson  # file sink
# or: check Splunk/Datadog/Elastic UI
```

Verified end-to-end in the Helix sandbox (548 events across two test runs,
state file advanced from PK 0 to PK 548, control change events visible
within 3 seconds).

## Event schema

Forwarded events have this shape (Datadog-compatible):

```json
{
    "timestamp": "2026-06-24 16:35:42.123456",
    "event_type": "appliedcontrol.update",
    "actor": {
        "id": 1,
        "email": "user@example.com"
    },
    "source": {
        "ip": "127.0.0.1"
    },
    "target": {
        "resource": "appliedcontrol",
        "action": "update",
        "object_id": "uuid-here"
    },
    "correlation_id": "django-auditlog-pk-1234",
    "changes": {
        "field_name": {"old": "x", "new": "y"}
    }
}
```

Datadog adds an envelope wrapper:

```json
{
    "ddsource": "ciso-assistant",
    "ddtags": "env:helix-sandbox,framework:hipaa",
    "hostname": "macbook.local",
    "message": "{...event above...}"
}
```

## State persistence

The forwarder writes its last-processed PK to
`~/.helix/audit_forwarder_state.json`. On restart it picks up where it
left off. Delete this file to force a full backfill.

## Configuration file

All flags can be set via YAML:

```yaml
db_path: /Users/ifeanyi/Documents/IJZ-Workspace/Tools/ciso-assistant-community/db/ciso-assistant.sqlite3
sink: datadog
poll_interval_seconds: 2
dd_api_key: ${DD_API_KEY}
dd_site: datadoghq.com
dd_tags:
    - env:helix-sandbox
    - framework:hipaa
```

```bash
python3 helix_audit_forwarder.py --config config.yaml
```

## Files

- `helix_audit_forwarder.py`  -  main daemon (698 lines)
- `datadog_api_contract.md`  -  HTTP contract for Datadog Logs API v2
- `com.helix.audit-forwarder.plist`  -  launchd plist for auto-restart
- `trigger_control_change.py`  -  test script that emits an audit event

## Datadog API contract

See `datadog_api_contract.md` for the full HTTP contract. Quick summary:

- **Endpoint:** `POST https://http-intake.logs.<DD_SITE>/api/v2/logs`
- **Auth:** `DD-API-KEY: <key>` header
- **Body:** NDJSON, one log per line
- **Rate limits:** Datadog allows up to 5MB per request, 1000 logs per
  request. The forwarder batches up to 500 events per POST.
- **TLS:** TLS 1.2+ required
- **Failover:** 4xx errors are dropped (no retry); 5xx errors are
  retried with exponential backoff up to 5 times