import uuid
from typing import Union, Optional

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
