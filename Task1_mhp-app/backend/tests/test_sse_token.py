"""
Smoke tests for F-1 / F-2 — SSE short-lived token auth.
Run from the backend/ directory:
    python tests/test_sse_token.py
The FastAPI server must already be running on http://localhost:8000.
"""

import sys
import requests

BASE = "http://localhost:8000"

PASS = "\033[32m[PASS]\033[0m"
FAIL = "\033[31m[FAIL]\033[0m"
failures = []


def check(label, condition, detail=""):
    if condition:
        print(f"{PASS} {label}")
    else:
        print(f"{FAIL} {label}  — {detail}")
        failures.append(label)


# ── 1. Login ──────────────────────────────────────────────────────────────────
r = requests.post(f"{BASE}/api/auth/login",
                  json={"email": "admin2@test.com", "password": "admin123"})
check("Login (200)", r.status_code == 200, f"{r.status_code} {r.text[:120]}")
if r.status_code != 200:
    sys.exit(1)

access_token = r.json()["access_token"]
auth_headers = {"Authorization": f"Bearer {access_token}"}

# ── 2. GET /api/auth/sse-token with valid Bearer ───────────────────────────────
r = requests.get(f"{BASE}/api/auth/sse-token", headers=auth_headers)
check("GET /sse-token (200)", r.status_code == 200, f"{r.status_code} {r.text[:120]}")

body = r.json() if r.status_code == 200 else {}
check("Response has 'token' field",   "token"      in body, str(body))
check("Response has 'expires_in'",    "expires_in" in body, str(body))
check("expires_in == 60",             body.get("expires_in") == 60, str(body))

sse_token = body.get("token", "")
print(f"       token length = {len(sse_token)}")

# ── 3. Unauthenticated call → 403 ────────────────────────────────────────────
r = requests.get(f"{BASE}/api/auth/sse-token")
check("No-auth guard (403)", r.status_code == 403,
      f"got {r.status_code}")

# ── 4. Open SSE stream — first use of the token (should succeed) ─────────────
r = requests.get(
    f"{BASE}/api/stream/headcount?token={sse_token}",
    stream=True, timeout=6,
)
# Do NOT access r.text — it would try to buffer an infinite SSE stream
check("SSE stream first-use (200)", r.status_code == 200,
      f"status={r.status_code}")

first_chunk = b""
if r.status_code == 200:
    try:
        for chunk in r.iter_content(chunk_size=None):
            first_chunk += chunk
            if b"data:" in first_chunk:
                break
    except Exception:
        pass
    finally:
        try:
            r.raw.connection.sock.close()
        except Exception:
            r.close()

check("SSE first event received", b"data:" in first_chunk,
      repr(first_chunk[:80]))

# ── 5. Replay attack — reuse the same token (should be rejected) ─────────────
r2 = requests.get(
    f"{BASE}/api/stream/headcount?token={sse_token}",
    stream=False, timeout=6,   # non-streaming: server sends 401 JSON immediately
)
check("Replay rejected (401)", r2.status_code == 401,
      f"got {r2.status_code}: {r2.text[:120]}")

# ── 6. Completely invalid token → 401 ────────────────────────────────────────
r3 = requests.get(
    f"{BASE}/api/stream/headcount?token=not.a.valid.token",
    stream=False, timeout=6,   # 401 JSON, not a stream
)
check("Bad token rejected (401)", r3.status_code == 401,
      f"got {r3.status_code}: {r3.text[:80]}")

# ── 7. New SSE token is usable on a fresh connection ─────────────────────────
r4 = requests.get(f"{BASE}/api/auth/sse-token", headers=auth_headers)
check("Second SSE token issued (200)", r4.status_code == 200,
      f"{r4.status_code}")
sse_token2 = r4.json().get("token", "") if r4.status_code == 200 else ""
check("Second token is different from first",
      sse_token2 != sse_token, "tokens are identical")

r5 = requests.get(
    f"{BASE}/api/stream/headcount?token={sse_token2}",
    stream=True, timeout=6,
)
check("Second SSE token connects (200)", r5.status_code == 200,
      f"status={r5.status_code}")
# Immediately abort the connection without reading any body
try:
    r5.raw.connection.sock.close()
except Exception:
    pass

# ── Summary ───────────────────────────────────────────────────────────────────
print()
if failures:
    print(f"  {len(failures)} test(s) FAILED: {', '.join(failures)}")
    sys.exit(1)
else:
    print("  All tests passed.")
