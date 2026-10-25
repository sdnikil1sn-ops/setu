
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

response = requests.post(
    f"{url}/auth/v1/token?grant_type=password",
    headers={"apikey": key, "Content-Type": "application/json"},
    json={"email": email, "password": password},
    timeout=20,
)

if response.status_code != 200:
    raise SystemExit(
        f"Supabase sign-in failed: HTTP {response.status_code}"
    )

token = response.json()["access_token"]
user_id = response.json().get("user", {}).get("id")

print("Supabase login: PASS")
print("Authenticated user ID:", user_id or "not returned")

headers = {"Authorization": f"Bearer {token}"}

for path in (
    "/api/v1/cases?limit=5",
    "/api/v1/cases?limit=5&bureau_id=__invalid_scope_test__",
):
    result = requests.get(
        "http://127.0.0.1:8081" + path,
        headers=headers,
        timeout=20,
    )
    print(f"{path}: HTTP {result.status_code}")

    if result.status_code == 200:
        try:
            data = result.json()
            items = data.get("items", [])
            print("  Returned records:", len(items))
            print("  Response keys:", list(data.keys()))
        except ValueError:
            print("  Response was not JSON.")
    else:
        try:
            print("  Detail:", str(result.json().get("detail", ""))[:150])
        except ValueError:
            print("  Error response was not JSON.")
