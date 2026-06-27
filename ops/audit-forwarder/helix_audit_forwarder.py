#!/usr/bin/env python3
"""
Helix Audit Log Forwarder

Polls CISO Assistant's django-auditlog LogEntry table (SQLite, WAL-safe reads)
and forwards each new entry to a configurable SIEM sink.

Sinks:
  - file:   Appends NDJSON to a local file (simulates SIEM for dev/test)
  - datadog: HTTP POST to Datadog Logs API v2 (https://http-intake.logs.datadoghq.com/api/v2/logs)
  - splunk:  HTTP POST to Splunk HEC (splunk_hec_url, channel header, token auth)
  - elastic: HTTP POST to Elasticsearch _bulk (NDJSON, Basic auth)

Swapping sinks is one config change (--sink <name> or SINK env var).

Usage:
  python3 helix_audit_forwarder.py --sink file --output /tmp/audit_log_sink.ndjson
  python3 helix_audit_forwarder.py --sink datadog --dd-api-key $DD_API_KEY
  python3 helix_audit_forwarder.py --config /path/to/config.yaml

Daemon: launchd plist included (com.helix.audit-forwarder.plist).

Author: Adeola (Systems & Automation Engineer)
Date: 2026-06-24
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import signal
import sqlite3
import sys
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

try:
    import requests
except ImportError:
    requests = None  # Only needed for HTTP sinks

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT, stream=sys.stderr)
logger = logging.getLogger("helix-forwarder")

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DEFAULT_DB_PATH = os.path.expanduser(
    "~/Documents/IJZ-Workspace/Tools/ciso-assistant-community/db/ciso-assistant.sqlite3"
)
DEFAULT_STATE_FILE = "/tmp/helix_audit_forwarder_state.json"
DEFAULT_OUTPUT_FILE = "/tmp/audit_log_sink.ndjson"
DEFAULT_POLL_INTERVAL = 5  # seconds

# Audit log action codes (django-auditlog)
ACTION_MAP = {0: "create", 1: "update", 2: "delete", 3: "access"}

# OCSF activity_id mapping (1=create, 2=read, 3=update, 4=delete)
OCSF_ACTIVITY_MAP = {0: 1, 1: 3, 2: 4, 3: 2}

# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------


@dataclass
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.helix.audit-forwarder</string>

    <key>ProgramArguments</key>
    <array>
        <string>/usr/local/bin/python3</string>
        <string>/Users/ifeanyi/Documents/IJZ-Workspace/Tools/helix-audit-forwarder/helix_audit_forwarder.py</string>
        <string>--sink</string>
        <string>file</string>
        <string>--output</string>
        <string>/tmp/audit_log_sink.ndjson</string>
        <string>--poll-interval</string>
        <string>5</string>
    </array>

    <!-- Install location for the forwarder script -->
    <!-- Copy helix_audit_forwarder.py to ~/Documents/IJZ-Workspace/Tools/helix-audit-forwarder/ -->

    <key>EnvironmentVariables</key>
    <dict>
        <!-- For Datadog sink, set the API key here or in keychain -->
        <!-- <key>DD_API_KEY</key> -->
        <!-- <string>YOUR_DATADOG_API_KEY</string> -->
        <!-- <key>SINK</key> -->
        <!-- <string>datadog</string> -->
    </dict>

    <key>RunAtLoad</key>
    <true/>

    <key>KeepAlive</key>
    <dict>
        <key>SuccessfulExit</key>
        <false/>
    </dict>

    <key>StandardOutPath</key>
    <string>/tmp/helix_audit_forwarder.log</string>

    <key>StandardErrorPath</key>
    <string>/tmp/helix_audit_forwarder.err</string>

    <key>ThrottleInterval</key>
    <integer>10</integer>
</dict>
</plist>
