from typing import Generator

from app.db.db import SessionLocal


async def get_db() -> Generator:
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()