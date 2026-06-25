#!/usr/bin/env python3
"""
risk_matrix_populate_5x5.py - populate an EXISTING RiskMatrix with a valid
5x5 ISO-27005 json_definition.

Use AFTER risk_matrix_create.py (which creates the matrix via Django ORM
because REST write path is broken on ReferentialSerializer.get_name_translated).
The ORM-bypass path can leave json_definition empty without any error, which
silently breaks every linked risk-scenario (their inherent_level and
residual_level fields evaluate to -1). This script is idempotent.

Container is read_only with cap_drop: ALL, no /scripts mount, so pipe in via stdin:

    SCRIPT=$(cat scripts/risk_matrix_populate_5x5.py)
    docker compose -f ~/Documents/IfeSec/Tools/ciso-assistant-community/docker-compose.yml \
        exec -T backend python -c "import sys; exec(sys.stdin.read())" <<< "$SCRIPT"

Helix-specific: matrix named "Helix Health 5x5". Edit MATRIX_NAME below
to target a different matrix.
"""
from __future__ import annotations

import json
import os
import sys

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ciso_assistant.settings")
django.setup()

from core.models import RiskMatrix  # noqa: E402

MATRIX_NAME = "Helix Health 5x5"

DEFINITION = {
    "probability": [
        {"id": 0, "abbreviation": "1", "name": "1 - unlikely",
         "description": "The likelihood of the risk scenario is very low"},
        {"id": 1, "abbreviation": "2", "name": "2 - rather unlikely",
         "description": "The likelihood of the risk scenario is low"},
        {"id": 2, "abbreviation": "3", "name": "3 - likely",
         "description": "The likelihood of the risk scenario is significant"},
        {"id": 3, "abbreviation": "4", "name": "4 - very likely",
         "description": "The likelihood of the risk scenario is high"},
        {"id": 4, "abbreviation": "5", "name": "5 - almost certain",
         "description": "The likelihood of the risk scenario is very high"},
    ],
    "impact": [
        {"id": 0, "abbreviation": "1", "name": "1 - minor",
         "description": "Negligible consequences for the organization"},
        {"id": 1, "abbreviation": "2", "name": "2 - significant",
         "description": "Significant but limited consequences for the organization"},
        {"id": 2, "abbreviation": "3", "name": "3 - serious",
         "description": "Substantial consequences for the organization"},
        {"id": 3, "abbreviation": "4", "name": "4 - critical",
         "description": "Disastrous consequences for the organization"},
        {"id": 4, "abbreviation": "5", "name": "5 - catastrophic",
         "description": "Sector or regulatory consequences beyond the organization"},
    ],
    "risk": [
        {"id": 0, "abbreviation": "1", "name": "1 - very low",
         "description": "very low - acceptable risk", "hexcolor": "#D3FF4E"},
        {"id": 1, "abbreviation": "2", "name": "2 - low",
         "description": "low - acceptable risk", "hexcolor": "#02A45A"},
        {"id": 2, "abbreviation": "3", "name": "3 - medium",
         "description": "medium - tolerable risk", "hexcolor": "#FFA600"},
        {"id": 3, "abbreviation": "4", "name": "4 - high",
         "description": "high - unacceptable risk", "hexcolor": "#FF1A00"},
        {"id": 4, "abbreviation": "5", "name": "5 - very high",
         "description": "very high - unacceptable risk", "hexcolor": "#C00000"},
    ],
    "grid": [
        [0, 0, 1, 1, 1],
        [0, 1, 1, 2, 2],
        [1, 1, 2, 3, 3],
        [1, 2, 3, 3, 4],
        [2, 3, 3, 4, 4],
    ],
    "type": "risk",
}


def main() -> int:
    try:
        matrix = RiskMatrix.objects.get(name=MATRIX_NAME)
    except RiskMatrix.DoesNotExist:
        print(f"ERROR: RiskMatrix named {MATRIX_NAME!r} not found", file=sys.stderr)
        return 1
    except RiskMatrix.MultipleObjectsReturned:
        print(f"ERROR: multiple RiskMatrix objects named {MATRIX_NAME!r}", file=sys.stderr)
        return 1

    before = matrix.json_definition
    if isinstance(before, str):
        try:
            before = json.loads(before)
        except Exception:
            before = {}
    prob_before = len(before.get("probability", [])) if isinstance(before, dict) else 0
    imp_before = len(before.get("impact", [])) if isinstance(before, dict) else 0
    grid_before = len(before.get("grid", [])) if isinstance(before, dict) else 0

    matrix.json_definition = DEFINITION
    matrix.save(update_fields=["json_definition"])

    matrix.refresh_from_db()
    after = matrix.json_definition
    if isinstance(after, str):
        after = json.loads(after)
    prob_after = len(after.get("probability", []))
    imp_after = len(after.get("impact", []))
    grid_after = len(after.get("grid", []))

    print(f"matrix_id          = {matrix.id}")
    print(f"matrix_name        = {matrix.name!r}")
    print(f"probability before = {prob_before}  after = {prob_after}")
    print(f"impact before      = {imp_before}  after = {imp_after}")
    print(f"grid before        = {grid_before} rows  after = {grid_after} rows")
    ok = prob_after == 5 and imp_after == 5 and grid_after == 5
    print(f"RESULT             = {'OK' if ok else 'FAIL'}")
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())
