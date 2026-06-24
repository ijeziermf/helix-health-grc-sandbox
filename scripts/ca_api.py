"""Minimal Python REST client for CISO Assistant v3.18.3.

Token auth via .mcp.env. Mirrors the AtlasPay ca_api.py verbatim so we have
the same working surface area across both sandboxes.

Usage:
    import ca_api
    count = ca_api.count("folders")
    folder = ca_api.find_by("folders", name="Helix Health")
    status, body = ca_api.post("folders/", {"name": "Helix Health",
                                              "parent_folder": "...",
                                              "content_type": "DOMAIN"})
"""
import json
import os
import re
import ssl
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import urljoin

ENV_PATH = Path(
    os.environ.get(
        "CA_ENV_PATH",
        "/Users/ifeanyi/Documents/IfeSec/Tools/ciso-assistant-community/cli/.mcp.env",
    )
)


def load_env() -> dict:
    env = {}
    for line in ENV_PATH.read_text().splitlines():
        if "=" in line:
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip().strip('"').strip("'")
    return env


def _ctx():
    return ssl._create_unverified_context()


def _req(method: str, endpoint: str, payload=None, params=None):
    env = load_env()
    api_url = env.get("API_URL", "https://localhost:8443/api").rstrip("/")
    token = env.get("TOKEN", "")
    url = f"{api_url}/{endpoint.lstrip('/')}"
    if params:
        url += "?" + "&".join(f"{k}={v}" for k, v in params.items())
    data = None
    headers = {"Authorization": f"Token {token}", "Accept": "application/json"}
    if payload is not None:
        data = json.dumps(payload).encode()
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, context=_ctx(), timeout=30) as r:
            body = r.read()
            return r.status, json.loads(body) if body else {}
    except urllib.error.HTTPError as e:
        body_text = e.read().decode("utf-8", errors="replace")
        try:
            body = json.loads(body_text)
        except Exception:
            body = {"raw": body_text}
        return e.code, body


def get(endpoint: str, params=None):
    status, body = _req("GET", endpoint, params=params)
    return body if status == 200 else {}


def post(endpoint: str, payload: dict):
    """Returns (status_code, body) tuple. Caller must unpack."""
    return _req("POST", endpoint, payload=payload)


def patch(endpoint: str, payload: dict):
    return _req("PATCH", endpoint, payload=payload)


def count(endpoint: str, params=None) -> int:
    body = get(endpoint, params={"limit": 1, **(params or {})})
    return body.get("count", 0)


def all_results(endpoint: str, params=None, page_size: int = 200) -> list:
    """Paginated list. DRF returns 'next' as relative path - strip /api before re-passing."""
    params = {**(params or {}), "limit": page_size}
    body = get(endpoint, params=params)
    results = body.get("results", [])
    next_url = body.get("next")
    while next_url:
        next_endpoint = re.sub(r"^/api/", "", next_url)
        next_endpoint = next_endpoint.split("?")[0]
        next_params = {}
        if "?" in next_url:
            for kv in next_url.split("?")[1].split("&"):
                if "=" in kv:
                    k, v = kv.split("=", 1)
                    next_params[k] = v
        body = get(next_endpoint, params=next_params)
        results.extend(body.get("results", []))
        next_url = body.get("next")
    return results


def find_by(endpoint: str, name: str, name_field: str = "name", folder: str = None) -> dict | None:
    """Find first record matching name. Optionally filter by folder field.

    Normalizes FK shape (CA returns {str, id} dicts on GET; we compare against
    bare UUID strings or denormalized dicts transparently).
    """
    for item in all_results(endpoint):
        if item.get(name_field) != name:
            continue
        if folder:
            f = item.get("folder") or {}
            folder_id = f.get("id") if isinstance(f, dict) else f
            if folder_id != folder:
                continue
        return item
    return None


def post_if_absent(endpoint: str, name: str, payload: dict, name_field: str = "name") -> tuple:
    """Idempotent create. Returns ("created"|"exists"|"error", body_dict)."""
    existing = find_by(endpoint, name=name, name_field=name_field)
    if existing:
        return "exists", existing
    status, body = post(endpoint, payload)
    if status not in (200, 201):
        return "error", body
    return "created", body
