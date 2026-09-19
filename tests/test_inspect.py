import asyncio
import sys
from pathlib import Path

# Ensure backend directory is in sys.path
backend_dir = Path(__file__).resolve().parents[1] / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from sqlalchemy import text
from app.db.session import engine


async def check():
    async with engine.connect() as conn:
        res = await conn.execute(
            text(
                "SELECT column_name FROM information_schema.columns WHERE table_name='students'"
            )
        )
        cols = [r[0] for r in res]
        print("students table columns:", cols)


if __name__ == "__main__":
    asyncio.run(check())
