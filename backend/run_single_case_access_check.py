
import getpass
import requests
from dotenv import dotenv_values

env = dotenv_values(".env")
url = (env.get("SUPABASE_URL") or "").rstrip("/")
key = env.get("SUPABASE_PUBLISHABLE_KEY") or ""

if not url or not key:
    raise SystemExit("Supabase configuration is missing.")

email = input("Test user's email: ").strip()
password = getpass.getpass("Test user's password (hidden): ")

try:
    login = requests.post(
        f"{url}/auth/v1/token?grant_type=password",
        headers={
            "apikey": key,
            "Content-Type": "application/json",
        },
        json={"email": email, "password": password},
        timeout=20,
    )
except requests.RequestException as exc:
    raise SystemExit(f"Login request failed: {type(exc).__name__}")

if login.status_code != 200:
    raise SystemExit(f"Login failed: HTTP {login.status_code}")

token = login.json().get("access_token")
if not token:
    raise SystemExit("No access token returned.")

headers = {"Authorization": f"Bearer {token}"}
base = "http://127.0.0.1:8081"

response = requests.get(
    f"{base}/api/v1/cases?limit=5",
    headers=headers,
    timeout=20,
)
print("Case list: HTTP", response.status_code)

if response.status_code != 200:
    raise SystemExit("Case-list request failed; stopping.")

items = response.json().get("items", [])

if items and items[0].get("case_id"):
    case_id = items[0]["case_id"]
    detail = requests.get(
        f"{base}/api/v1/cases/{case_id}",
        headers=headers,
        timeout=20,
    )
    print("Returned case detail: HTTP", detail.status_code)
else:
    print("No case ID returned; single-case test skipped.")

missing = requests.get(
    f"{base}/api/v1/cases/SETU-NONEXISTENT-CASE-TEST",
    headers=headers,
    timeout=20,
)
print("Nonexistent case: HTTP", missing.status_code)
