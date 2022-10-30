import uuid
from datetime import timedelta
from typing import Union, Optional, List

from pydantic import BaseModel
from pydantic.schema import datetime

IdType = Union[str, int, uuid.UUID]


class SourceDB(BaseModel):
    id: IdType
    name: Optional[str]
    filepath: str
    created: Optional[datetime]

    class Config:
        orm_mode=True


class SourceRead(SourceDB):
    pass


###############################
class Verse(BaseModel):
    VerseId: int
    Text: str


class Chapter(BaseModel):
    ChapterId: int
    Verses: list[Verse]


class Book(BaseModel):
    BookId: int
    Chapters: list[Chapter]


class Bible(BaseModel):
    Translation: Optional[str]
    Books: Optional[list[Book]]


class BibleFlat(BaseModel):
    book_id: int
    chapter_id: int
    verse_id: int
    verse_text: str


class Result(BaseModel):
    text: str
    similarity: float

    book_id: Optional[int]
    chapter_id: Optional[int]
    verse_id: Optional[int]


class ResponseDocs(BaseModel):
    query: str
    time_processed: timedelta
    results_limit: int
    results: List[Result]

