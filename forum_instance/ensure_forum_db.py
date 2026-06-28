import os
import sys
import time

import psycopg


def get_env(name, default=None):
    return os.environ.get(name, default)


DB_NAME = get_env("FORUM_POSTGRES_DB", "agroforum")
DB_USER = get_env("FORUM_POSTGRES_USER", "agr")
DB_PASS = get_env("FORUM_POSTGRES_PASSWORD", "")
DB_HOST = get_env("FORUM_POSTGRES_HOST", "db")
DB_PORT = int(get_env("FORUM_POSTGRES_PORT", 5432))

RETRIES = 30
SLEEP = 2


def ensure_db():
    last_err = None
    for attempt in range(1, RETRIES + 1):
        try:
            # Connect to the server using the default 'postgres' database
            conn = psycopg.connect(
                dbname="postgres",
                user=DB_USER,
                password=DB_PASS,
                host=DB_HOST,
                port=DB_PORT,
                connect_timeout=5,
            )
            conn.autocommit = True
            with conn.cursor() as cur:
                cur.execute("SELECT 1 FROM pg_database WHERE datname=%s;", (DB_NAME,))
                exists = cur.fetchone() is not None
                if exists:
                    print(f"Database '{DB_NAME}' already exists")
                else:
                    print(f"Creating database '{DB_NAME}'")
                    cur.execute(f'CREATE DATABASE "{DB_NAME}" OWNER {DB_USER};')
            conn.close()
            return True
        except Exception as e:
            last_err = e
            print(f"Attempt {attempt}/{RETRIES}: database not ready or cannot create DB: {e}")
            time.sleep(SLEEP)
    print(f"Failed to ensure database exists after {RETRIES} attempts: {last_err}")
    return False


if __name__ == "__main__":
    ok = ensure_db()
    if not ok:
        # Exit non-zero so container startup can still continue but user sees error
        print("Warning: could not ensure forum database exists; continuing anyway")
        sys.exit(0)
    else:
        sys.exit(0)
