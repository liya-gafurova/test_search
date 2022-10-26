from typing import Optional

from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from starlette import status
from starlette.responses import Response

from app.crud.sources import crud_sources
from app.deps import get_db, get_searching_instruments, SearchingEntity
from app.domain.commands import query_command, get_bible, get_small_bible, index_command
from app.domain.utils import get_file_url, generate_uuid, save_file, read_json,  save_json
from app.schemas import IdType, SourceDB, Bible, BibleFlat

router_source = APIRouter()
router_query = APIRouter()


@router_source.post('/delete')
async def delete_source_data(id: IdType):
    pass


@router_source.get('')
async def get_all_resources(skip:int = 0, limit: int = 10, db = Depends(get_db)):
    sources = crud_sources.get_multi(db=db, skip=skip, limit=limit)

    return sources


@router_source.post('/upload')
async def upload_source_data(
        source_name: Optional[str], file: UploadFile = File(...), db=Depends(get_db)
):
    filepath = get_file_url(file.filename)
    await save_file(filepath, file)

    source = SourceDB(id=generate_uuid(), name=source_name, filepath=filepath)
    obj = crud_sources.create(db=db, obj_in=source)

    return obj


@router_source.get('/{id}')
async def get_source(id: IdType, db = Depends(get_db)):
    source = crud_sources.get(db=db, id=id)

    return source


@router_source.post('/{id}/index')
async def index_data(id: IdType, db=Depends(get_db), searching_inst = Depends(get_searching_instruments)):
    small_bible_path = "/home/lia/PycharmProjects/bible_search/data/SMALL_bible_large_20221024232834.json"
    data: dict = read_json(small_bible_path)
    bible: Bible = get_bible(data)

    verses = []

    for b in bible.Books:
        for c in b.Chapters:
            for v in c.Verses:
                verses.append(
                    BibleFlat(verse_text=v.Text, book_id=b.BookId, chapter_id=c.ChapterId, verse_id=v.VerseId)
                )

    index_command(verses, searching_inst)


@router_source.post('/{id}/create/small')
async def get_small_bible_version(
        id: IdType, books_max: int = 10, chapters_max: int = 10, verses_max: int = 10, db=Depends(get_db)
):
    source = crud_sources.get(db, id)

    if not source:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    bible_data: dict = read_json(source.filepath)
    bible: Bible = get_bible(bible_data)
    small_version: Bible = get_small_bible(bible, books_max, chapters_max, verses_max)
    small_bible_data: dict = small_version.json(ensure_ascii=False)
    new_filepath = get_file_url(f'SMALL_{source.name}.json')
    await save_json(new_filepath, small_bible_data)

    new_source = crud_sources.create(db=db, obj_in=SourceDB(id=generate_uuid(),
                                                            name=f'SMALL_{source.name}',
                                                            filepath=new_filepath))
    return new_source


@router_source.post('/{id}/indexed/delete')
async def delete_indexed_data(id: Optional[IdType], searching_inst: SearchingEntity = Depends(get_searching_instruments)):

    searching_inst.indexed_data.clear()
    searching_inst.indexed_data.summary()

    return Response(status_code=status.HTTP_200_OK)


@router_query.post('/send')
async def send_query(query: str, searching_instruments = Depends(get_searching_instruments)):
    answer = query_command(query, searching_instruments)

    return answer
