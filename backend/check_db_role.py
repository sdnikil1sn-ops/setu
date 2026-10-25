import os
from pathlib import Path

import psycopg
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")

database_url = os.getenv("DATABASE_URL")

if not database_url:
    raise SystemExit("DATABASE_URL is not configured.")

with psycopg.connect(database_url) as conn:
    with conn.cursor() as cur:
        cur.execute("""
            SELECT
                current_user,
                r.rolsuper,
                r.rolbypassrls
            FROM pg_roles AS r
            WHERE r.rolname = current_user;
        """)
        result = cur.fetchone()

if result:
    print("Database role:", result[0])
    print("Superuser:", result[1])
    print("Bypasses RLS:", result[2])
else:
    print("Could not identify the active database role.")