# Helix Health Lessons Learned

These are the non-obvious findings from ingesting the Helix Health persona
into CISO Assistant v3.18.3. They are the differences between what the docs
say and what actually works in this environment.

## 1. ORM-bypass is required for risk matrix creation

The REST endpoint `POST /api/risk-matrices/` accepts the data but the
`json_definition` field is silently dropped or rejected. Workaround:

```bash
docker exec backend python -c "
import django, os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ciso_assistant.settings')
django.setup()
from core.models import RiskMatrix
m = RiskMatrix.objects.create(
    name='5x5 ISO-27005',
    folder=<helix_folder_id>,
    json_definition={'name': '5x5', 'type': 'risk', 'fields': {...}}
)
"
```

See `scripts/risk_matrix_populate_5x5.py` for the full template.

## 2. Risk scenario level fields require ORM-bypass

The REST `POST /api/risk-scenarios/` accepts `inherent_proba`, `inherent_impact`,
`current_proba`, `current_impact`, `residual_proba`, `residual_impact` as
integers (0-4) but does NOT persist them. The `level` field is auto-computed
from a matrix lookup and silently stays unset.

Workaround: create via REST, then update via ORM with the int fields.

## 3. Folder filter on REST API is broken

`GET /api/risk-scenarios/?folder=<id>` returns ALL folders, not filtered.
The `folder` field is nested `{str, id}` object and the query param doesn't
match nested fields.

Workaround: fetch all and filter client-side, or use ORM.

## 4. Auth endpoint

Login is `POST /api/_allauth/app/v1/auth/login` (no trailing slash).
The trailing slash returns 404.

The session cookie returned (`sessionid`) plus the `token` cookie work
for both client-side hydration and API calls. The CSRF cookie must be
included in any state-changing request.

## 5. Real route names

- `/risk-scenarios` (not `/risks`)
- `/perimeters` (not `/perimeter`)
- `/applied-controls` (not `/controls`)
- `/risk-assessments` (not `/risk-assessments-list`)

The sidebar nav uses these names but the URL slugs are different.

## 6. Playwright `install` fails

`playwright install` fails because the bundled Chromium download is blocked
in this environment. Use system Chrome instead:

```python
browser = p.chromium.launch(
    executable_path='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
    headless=True,
)
```

## 7. Token storage in the `token` cookie

The `token` cookie is set by login and works for client-side hydration
even when server-side SSR data fetches return 401. Set it via the JS
console after login and the SPA hydrates correctly.

## 8. APFS dataless state

The Mac's APFS filesystem can produce files that exist but cannot be read
without `xattr -c` and `cp -c` to a new path. Symptom: file has bytes
according to `ls -la` but `cat` or `python read` returns 0 bytes or
Resource deadlock. Fix:

```bash
xattr -c /path/to/file
cp -c /path/to/file /new/path/
```

If that doesn't work, run `brctl download /path/to/directory/` to
materialize the dataless files via iCloud.

## 9. ORM `save()` doesn't always trigger matrix level recomputation

When updating risk scenario levels via ORM, you must explicitly trigger
the matrix recalculation or the displayed level stays stale. Pass
`update_level=True` if available, or call the matrix's `_compute()`
method directly.

## 10. Container access

The `backend` container is the only one with Python access. Use:

```bash
docker exec backend python -c "<script>"
```

This is what `docker exec backend python -c "..."` returns for `script`.

## 11. Docker stack restart order

Caddy must come up after frontend/backend. If Caddy comes up first and
the backends aren't ready, Caddy serves 502s for ~30 seconds before
backends are healthy. The docker-compose file already handles this via
`depends_on` with `condition: service_healthy`.

## 12. SQLite WAL mode

CISO Assistant uses SQLite in WAL mode for concurrent reads. The
`audit_log_forwarder` reads this DB and must use WAL-safe reads (no
exclusive locks, no `BEGIN IMMEDIATE`).

## 13. Frameworks must be loaded BEFORE folders are created

Framework URNs are global, not folder-scoped. But when you create a
risk scenario and assign it to a folder, the folder must already
exist. So the order is:

1. POST `/api/loaded-libraries/` for each framework URN
2. POST `/api/folders/` for the domain folder
3. POST `/api/perimeters/` (linked to folder)
4. POST `/api/risk-matrices/` (linked to folder) — but use ORM for json_definition
5. POST `/api/risk-scenarios/`
6. POST `/api/policies/`
7. POST `/api/entities/`
8. POST `/api/contracts/`
9. POST `/api/privacy/processings/`
10. POST `/api/validation-flows/`

## 14. Priority and CSF function enums

- `priority`: int 1-4 (1=highest, 4=lowest)
- `csf_function`: lowercase string — `identify`, `protect`, `detect`,
  `respond`, `recover` — NOT uppercase

If you send `Protect` (uppercase), the API returns 400.

## 15. The cron daemon environment is stripped

`bash -c "source .mcp.env && echo $TOKEN"` works in interactive shells
but fails in the cron daemon's stripped environment. Always read env
files directly in Python, not via `source`.

## See also

- `docs/00-setup.md` — CISO Assistant Docker install walkthrough
- `~/.hermes/skills/grc/ciso-assistant-sandbox-setup/references/orm-bypass-patterns.md` — full ORM patterns
- `~/.hermes/skills/grc/ciso-assistant-sandbox-setup/references/risk-matrix-schema.md` — canonical matrix format