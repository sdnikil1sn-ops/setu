
import os

import psycopg
from dotenv import load_dotenv

load_dotenv()

database_url = os.getenv("DATABASE_URL")

if not database_url:
    raise RuntimeError(
        "DATABASE_URL is missing. Check your .env file."
    )

with psycopg.connect(database_url, connect_timeout=15) as conn:
    with conn.cursor() as cur:
        cur.execute(
            "SELECT current_database(), current_user, version()"
        )
        database, user, version = cur.fetchone()

print("Connection successful!")
print("Database:", database)
print("Connected role:", user)
print("PostgreSQL version:", version.split(",")[0])
