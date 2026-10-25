
import getpass
import json
import os
import time
import urllib.error
import urllib.request
import jwt

from dotenv import load_dotenv


load_dotenv(".env")

SUPABASE_URL = os.getenv("SUPABASE_URL", "").rstrip("/")
SUPABASE_KEY = os.getenv("SUPABASE_PUBLISHABLE_KEY", "")
SETU_API_URL = "http://127.0.0.1:8081"


def post_json(url, payload, headers):
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=data,
        headers={
            **headers,
            "Content-Type": "application/json",
        },
        method="POST",
    )

    with urllib.request.urlopen(request, timeout=15) as response:
        return json.loads(response.read().decode("utf-8"))


def main():
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("FAIL: Supabase URL or publishable key is missing.")
        return

    email = input("Test account email: ").strip()
    password = getpass.getpass("Test account password: ")

    access_token = None

    try:
        result = post_json(
            f"{SUPABASE_URL}/auth/v1/token?grant_type=password",
            {
                "email": email,
                "password": password,
            },
            {"apikey": SUPABASE_KEY},
        )

        access_token = result.get("access_token")

        if not access_token:
            print("FAIL: Supabase did not return an access token.")
            return

        print("PASS: Supabase sign-in succeeded.")
                # Diagnostic only: never use an unverified header to authenticate.
        header = jwt.get_unverified_header(access_token)
        print("Token algorithm:", header.get("alg"))
        print("Token key ID present:", bool(header.get("kid")))
        
        import time
        claims = jwt.decode(
    access_token,
    options={"verify_signature": False},
)
        now = time.time()
        for name in ("iat", "nbf", "exp"):
            value = claims.get(name)

            if isinstance(value, (int, float)):
                difference = value - now
                print(f"{name}: {difference:+.1f} seconds relative to current time")
            else:
                print(f"{name}: absent or invalid type")
    
        from auth import verify_supabase_jwt

        try:
            verify_supabase_jwt(access_token)
            print("PASS: Local JWT signature and claims verified.")
        except Exception as exc:
            print("Local JWT verification failed.")
            print("Error type:", type(exc).__name__)

        request = urllib.request.Request(
            f"{SETU_API_URL}/api/v1/cases?limit=1",
            headers={"Authorization": f"Bearer {access_token}"},
        )

        with urllib.request.urlopen(request, timeout=20) as response:
            print(f"SETU API HTTP status: {response.status}")

            if response.status == 200:
                print("PASS: SETU accepted the real Supabase access token.")
            else:
                print("FAIL: SETU returned an unexpected status.")

    except urllib.error.HTTPError as exc:
        print(f"HTTP request failed with status {exc.code}.")
        print("Check the test account, Supabase Auth configuration,")
        print("and whether the SETU API server is running.")
    except urllib.error.URLError:
        print("Connection failed. Check the Supabase URL and API server.")
    finally:
        access_token = None
        password = None


if __name__ == "__main__":
    main()
