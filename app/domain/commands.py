from app.schemas import Bible, Chapter, Book


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
