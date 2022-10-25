from typing import List

from docarray import DocumentArray, Document

from app.deps import SearchingEntity
from app.schemas import Bible, Chapter, Book, BibleFlat


def get_bible(bible_json: dict) -> Bible:
    return Bible.parse_obj(bible_json)


def get_small_bible(
        bible: Bible, books: int = 10, chapters: int = 10, verses: int = 10
    ) -> Bible:

    new_bible_obj = Bible(Translation=bible.Translation, Books=[])

    bs, chs, vs, = [], [], []
    new_chapter = None
    new_book = None

    for i, book in enumerate(bible.Books):

        for j, chapter in enumerate(book.Chapters):

            for k, verse in enumerate(chapter.Verses):
                vs.append(verse)

                if k > verses:
                    new_chapter = Chapter(ChapterId=chapter.ChapterId, Verses=vs)
                    vs = []
                    break

            chs.append(new_chapter)

            if j > chapters:
                new_book = Book(BookId=book.BookId, Chapters=chs)
                chs = []
                break

        bs.append(new_book)

        if i > books:
            new_bible_obj.Books = bs
            break

    return new_bible_obj


def query_command(query_phrase: str, searching_entity: SearchingEntity):
    searching_entity.indexed_data.summary()

    da_query = DocumentArray([Document(text=query_phrase)])
    da_query.embed(searching_entity.model, collate_fn=searching_entity.collate_fn)

    res: List[DocumentArray] = searching_entity.indexed_data.find(da_query, metric='cosine', limit=3)

    res[0].summary()

    return res[0]


def index_command(data: BibleFlat, searching_inst: SearchingEntity):
    for id, text in data.items():
        searching_inst.indexed_data.append(Document(text=text, id=id))

    searching_inst.indexed_data.embed(searching_inst.model, collate_fn=searching_inst.collate_fn)