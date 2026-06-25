from datetime import datetime, timezone
def api_request(path, method="GET", data=None, csrf_token=None):
    url = f"{BASE}{path}"
    headers = {
        "Accept": "application/json",
    }
    if data is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(data).encode()
    if csrf_token:
        headers["X-CSRFToken"] = csrf_token
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        resp = opener.open(req, timeout=15)
        body = resp.read().decode()
        return resp.status, json.loads(body) if body else {}
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()[:500]

+# Step 1: Get CSRF token first
status, csrf_data = api_request("/api/csrf/")
csrf_token = csrf_data.get("csrfToken", "") if isinstance(csrf_data, dict) else ""
print(f"CSRF: {status} token={csrf_token[:20]}...")

+# Step 2: Login with CSRF
status, login_resp = api_request(
    "/api/_allauth/browser/v1/auth/login",
    data={"email": EMAIL, "password": PASSWORD},
    csrf_token=csrf_token,
print(f"Login: {status}")
if status != 200:
    print(f"  error: {login_resp}")
# Step 3: Get CSRF again (session may have refreshed it)
status, csrf_data = api_request("/api/csrf/")
csrf_token = csrf_data.get("csrfToken", "") if isinstance(csrf_data, dict) else ""
print(f"CSRF post-login: {status} token={csrf_token[:20]}...")
