"""Manual read-only database connectivity diagnostic.

Run with ``python test_db.py`` when DATABASE_URL is configured. This is
intentionally guarded so pytest collection never contacts a live database.
"""

import os
from pathlib import Path

import psycopg
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


def main():
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL is missing. Check backend/.env.")

    with psycopg.connect(database_url, connect_timeout=15) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT current_database(), current_user, version()")
            database, user, version = cur.fetchone()

    print("Connection successful!")
    print("Database:", database)
    print("Connected role:", user)
    print("PostgreSQL version:", version.split(",")[0])


if __name__ == "__main__":
    main()
