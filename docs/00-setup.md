# Helix Health GRC Sandbox — Setup

This is the setup walkthrough for running the Helix Health persona
against CISO Assistant v3.18.3 on macOS via Docker Desktop.

## Prerequisites

- macOS 26.x (Apple Silicon verified)
- Docker Desktop 4.x with at least 4 GB allocated
- ~10 GB free disk space (CISO Assistant stack + audit log samples)
- Ports 8443 and 9443 free
- Git 2.3+

## Step 1: Clone and bring up the stack

```bash
git clone https://github.com/ijeziermf/helix-health-grc-sandbox.git
cd helix-health-grc-sandbox

docker compose up -d
```

Wait ~30 seconds for the backend to complete migrations.

```bash
sleep 30
curl -sk -o /dev/null -w '%{http_code}\n' https://localhost:8443/api/health/
# expect: 200
```

## Step 2: Log in

Default credentials:

- **URL:** https://localhost:8443
- **Email:** ijeziermf@gmail.com
- **Password:** 8950Fourth

You'll be prompted to change the password on first login.

## Step 3: Run the Helix Health ingestion

The ingestion scripts in `scripts/` are idempotent — they create-or-update
on each run. Run them in order:

```bash
# Load the 5 frameworks (HIPAA Security Rule via NIST SP-800-66, HDS v2.0,
# SOC 2 TSC 2022, NIST CSF 2.0, ISO 27001:2022)
python3 scripts/ingest_helix.py --phase frameworks

# Create the Helix Health folder, 3 perimeters, 5x5 risk matrix, risk
# assessment, 12 risk scenarios, 12 policies, 10 vendors, 10 contracts
python3 scripts/ingest_helix.py --phase core

# Phase 1B: 15 ROPA processing activities + 5 validation flows
python3 scripts/ingest_helix_phase1b.py

# ORM bypass for risk scenario level fields (REST endpoint doesn't
# persist them)
docker exec backend python -c "
import django, os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ciso_assistant.settings')
django.setup()
from core.models import RiskScenario
for rs in RiskScenario.objects.filter(folder__name='Helix Health'):
    rs.inherent_proba = 3
    rs.inherent_impact = 4
    rs.current_proba = 1
    rs.current_impact = 1
    rs.residual_proba = 1
    rs.residual_impact = 1
    rs.save()
print('Updated', RiskScenario.objects.filter(folder__name='Helix Health').count())
"
```

## Step 4: Verify the data

```bash
python3 scripts/capture_helix_state.py
# Generates screenshots in screenshots/ and a state JSON dump
```

Or hit the API directly:

```bash
TOKEN=*** https://localhost:8443/api/health/

# Count Helix-specific objects
curl -sk -H "Authorization: Token *** \
    "https://localhost:8443/api/folders/?limit=100" \
  | jq '.results[] | select(.name=="Helix Health") | .id'

# Use that ID to filter risk-scenarios, policies, etc.
```

## Step 5: Generate the portfolio PDF

```bash
python3 deliverables/generate_portfolio_pdf.py
# Outputs deliverables/Helix_Health_Portfolio_v2.pdf (~1 MB)
```

## Step 6: Start the audit log forwarder (optional)

```bash
# Install the launchd plist
cp ops/audit-forwarder/com.helix.audit-forwarder.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.helix.audit-forwarder.plist

# Verify it's running
launchctl list | grep audit-forwarder

# Trigger a test event
python3 ops/audit-forwarder/trigger_control_change.py

# Check the sink
tail -n 1 /var/log/helix/audit.ndjson
```

## Troubleshooting

### "Port 8443 already in use"

Stop any service on 8443 first. Common culprits:
- Other Docker containers (run `docker ps` to check)
- macOS AirPlay Receiver (set to listen on a different port)

### "Backend unhealthy"

```bash
docker compose logs backend --tail 50
```

Common issues:
- SQLite DB locked by another process (rare; CISO Assistant uses WAL mode)
- SECRET_KEY missing (check the .env file in `ciso-assistant-community/`)
- DB file permissions

### "Login fails with 401"

The auth endpoint requires `POST /api/_allauth/app/v1/auth/login` (no
trailing slash). With trailing slash: 404.

### "Risk scenario levels not displayed"

The REST endpoint doesn't persist the level fields. Use the ORM-bypass
pattern shown in Step 3 above.

### "Playwright fails to launch"

Use system Chrome:
```python
browser = p.chromium.launch(executable_path='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome')
```

## Cleanup

```bash
docker compose down -v
# Removes containers AND the SQLite volume
```

To preserve the data between rebuilds:

```bash
docker compose down
# Stops containers but keeps the SQLite file
```