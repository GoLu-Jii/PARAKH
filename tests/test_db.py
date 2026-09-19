import asyncio
import sys
from pathlib import Path

# Ensure backend directory is in sys.path
backend_dir = Path(__file__).resolve().parents[1] / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from sqlalchemy import text
from app.db.session import engine


async def test_connection():
    async with engine.connect() as connection:
        result = await connection.execute(text("SELECT 1"))
        print("Database connection successful:", result.scalar())


if __name__ == "__main__":
    asyncio.run(test_connection())
