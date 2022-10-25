from typing import Generator

from docarray import DocumentArray

from app.db.db import SessionLocal
from app.domain.nn import model_rubert, tokenizer_rubert
from app.domain.storage import document_array_qdrant


async def get_db() -> Generator:
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()


class SearchingEntity:
    model = model_rubert
    tokenizer = tokenizer_rubert
    indexed_data = document_array_qdrant

    def collate_fn(self, da: DocumentArray):
        res = tokenizer_rubert(da.texts, return_tensors="pt", truncation=True, padding=True)
        return res


async def get_searching_instruments() -> SearchingEntity:
    return SearchingEntity()
