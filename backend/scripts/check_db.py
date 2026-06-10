"""Test database connectivity. Run from backend/: python scripts/check_db.py"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import text

from app.core.config import settings
from app.db.session import engine


def main() -> None:
    print(f"Connecting to: {settings.database_url.split('@')[-1]}")
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("OK — database is reachable.")
    except Exception as e:
        print("FAILED —", e)
        print()
        print("Common fixes:")
        print("  1. docker compose up -d   (from project root)")
        print("  2. Use port 5433 in backend/.env (avoids local Postgres on 5432)")
        print("  3. copy .env.example .env if .env is missing")
        sys.exit(1)


if __name__ == "__main__":
    main()
