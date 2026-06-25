#!/usr/bin/env python3
"""
risk_matrix_and_assessment_create.py - create the Helix Health 5x5 RiskMatrix
and the parent RiskAssessment container via Django ORM.

Why ORM and not REST:
  - REST write path is broken for RiskMatrix and RiskAssessment due to
    backend/core/serializers.py:215: name = serializers.CharField(source="get_name_translated")
    where get_name_translated is a @property without a setter (verified 2026-06-23).
  - POST without name -> 400, POST with name -> 500 AttributeError.

Usage:
    SCRIPT=$(cat scripts/risk_matrix_and_assessment_create.py)
    docker compose -f ~/Documents/IfeSec/Tools/ciso-assistant-community/docker-compose.yml \
        exec -T backend python -c "import sys; exec(sys.stdin.read())" <<< "$SCRIPT"

Both records are idempotent: re-running prints EXISTS line and exits 0.
"""
from __future__ import annotations

import os
import sys
from datetime import date, timedelta

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ciso_assistant.settings")
django.setup()

from core.models import Folder, RiskAssessment, RiskMatrix  # noqa: E402

MATRIX_NAME = "Helix Health 5x5"
MATRIX_URN = "urn:intuitem:risk:matrix:helix-5x5"
MATRIX_DESC = "Standard 5x5 risk matrix (probability x impact) for Helix Health GRC."

RA_NAME = "Helix HIPAA + SOC 2 Readiness Risk Assessment"
RA_URN = "urn:intuitem:risk:assessment:helix-hipaa-soc2"
RA_DESC = (
    "Container risk assessment for Helix Health. Drives HIPAA Security Rule "
    "and SOC 2 Type 2 readiness, with HITRUST CSF v11 cross-references."
)


def main() -> int:
    # --- RiskMatrix (idempotent) ---
    matrix = RiskMatrix.objects.filter(name=MATRIX_NAME).first()
    if matrix:
        print(f"MATRIX_EXISTS id={matrix.id} urn={matrix.urn}")
    else:
        matrix = RiskMatrix.objects.create(
            name=MATRIX_NAME,
            description=MATRIX_DESC,
            ref_id="RM-HELIX-5X5",
            urn=MATRIX_URN,
            provider="custom",
            editing_draft={
                "probability": [
                    {"abbreviation": str(i), "name": f"P{i}", "description": f"Level {i}"}
                    for i in range(1, 6)
                ],
                "impact": [
                    {"abbreviation": str(i), "name": f"I{i}", "description": f"Level {i}"}
                    for i in range(1, 6)
                ],
                "type": "5x5",
            },
            is_published=True,
        )
        print(f"MATRIX_CREATED id={matrix.id} urn={matrix.urn}")

    # --- RiskAssessment (idempotent) ---
    ra = RiskAssessment.objects.filter(name=RA_NAME).first()
    if ra:
        print(f"RA_EXISTS id={ra.id} matrix_id={ra.risk_matrix_id}")
    else:
        folder = Folder.objects.get(name="Helix Health")
        ra = RiskAssessment.objects.create(
            name=RA_NAME,
            description=RA_DESC,
            ref_id="RA-HELIX-HIPAA-SOC2",
            status="in_progress",
            version="1.0",
            eta=date.today() + timedelta(days=90),
            due_date=date.today() + timedelta(days=180),
            risk_tolerance=4,
            folder=folder,
            risk_matrix=matrix,
        )
        print(f"RA_CREATED id={ra.id} matrix_id={matrix.id}")

    print("RESULT OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
