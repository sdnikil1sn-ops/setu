
import getpass
import requests
from dotenv import dotenv_values

env = dotenv_values(".env")
url = (env.get("SUPABASE_URL") or "").rstrip("/")
key = env.get("SUPABASE_PUBLISHABLE_KEY") or ""

if not url or not key:
    raise SystemExit("Supabase URL or publishable key is missing.")

email = input("Test user's email: ").strip()
password = getpass.getpass("Test user's password (hidden): ")

try:
    response = requests.post(
        f"{url}/auth/v1/token?grant_type=password",
        headers={
            "apikey": key,
            "Content-Type": "application/json",
        },
        json={"email": email, "password": password},
        timeout=20,
    )
except requests.RequestException as exc:
    raise SystemExit(
        f"Supabase Auth request failed: {type(exc).__name__}"
    )

if response.status_code != 200:
    try:
        body = response.json()
        detail = (
            body.get("msg")
            or body.get("message")
            or body.get("error_description")
            or body.get("error")
            or "Sign-in failed"
        )
    except ValueError:
        detail = "Sign-in failed"

    raise SystemExit(
        f"Sign-in failed (HTTP {response.status_code}): {detail}"
    )

token = response.json().get("access_token")
if not token:
    raise SystemExit("No access token was returned.")

print("\nSupabase sign-in succeeded.")
print("Access token obtained; its value will not be displayed.")

base = "http://127.0.0.1:8081"

for path in (
    "/api/v1/institutions",
    "/api/v1/summary",
    "/api/v1/cases",
):
    try:
        result = requests.get(
            base + path,
            headers={"Authorization": f"Bearer {token}"},
            timeout=20,
        )
        print(f"{path}: HTTP {result.status_code}")

        if result.status_code >= 400:
            try:
                detail = result.json().get(
                    "detail", "Request rejected"
                )
            except ValueError:
                detail = "Non-JSON error response"

            print("  Detail:", str(detail)[:200])

    except requests.RequestException as exc:
        print(f"{path}: Request failed ({type(exc).__name__})")
