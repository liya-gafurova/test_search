from typing import Optional

from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from starlette import status
from starlette.background import BackgroundTasks
from starlette.responses import Response

from app.crud.sources import crud_sources
from app.deps import get_db, get_searching_instruments, SearchingEntity, en_search_inst
from app.domain.commands import *
from app.domain.utils import get_file_url, generate_uuid, save_file, read_json, save_json
from app.schemas import IdType, SourceDB, Bible, BibleFlat

router_source = APIRouter()
router_indexed = APIRouter()
router_query = APIRouter()


@router_source.get('')
async def get_all_resources(skip: int = 0, limit: int = 10, db=Depends(get_db)):
    sources = crud_sources.get_multi(db=db, skip=skip, limit=limit)

    return sources


@router_source.get('/{id}')
async def get_source(id: IdType, db=Depends(get_db)):
    source = crud_sources.get(db=db, id=id)

    return source


@router_source.post('/upload')
async def upload_source_data(
        source_name: Optional[str],
        lang: Lang,
        translation: Translation,
        file: UploadFile = File(...),
        db=Depends(get_db)
):
    if translation not in rules[lang]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail='Language and translation are not matching.')

    filepath = get_file_url(file.filename)
    await save_file(filepath, file)

    source = SourceDB(id=generate_uuid(),
                      name=source_name,
                      filepath=filepath,
                      lang=lang.value,
                      translation_type=translation.value)

    obj = crud_sources.create(db=db, obj_in=source)

    return obj


@router_source.post('/{id}/generate/small')
async def get_small_bible_version(
        id: IdType, books_max: int = 5, chapters_max: int = 5, verses_max: int = 5, db=Depends(get_db)
):
    readers = {
        Lang.RUS: get_bible,
        Lang.EN: get_en_bible,
    }
    source = crud_sources.get(db, id)

    if not source:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    reader = readers[source.lang]

    bible_data: dict = read_json(source.filepath)
    bible: Bible = reader(bible_data, transaltion=source.translation_type)
    small_version: Bible = get_small_bible(bible, books_max, chapters_max, verses_max)
    small_bible_data: dict = small_version.json(ensure_ascii=False)
    new_filepath = get_file_url(f'SMALL_{source.name}.json')
    await save_json(new_filepath, small_bible_data)

    new_source = crud_sources.create(db=db, obj_in=SourceDB(id=generate_uuid(),
                                                            name=f'SMALL_{source.name}',
                                                            filepath=new_filepath))
    return new_source


@router_source.delete('/delete')
async def delete_source_data(id: IdType, db = Depends(get_db)):
    source = crud_sources.get(db=db, id=id)
    if not source:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    deleted = crud_sources.remove(db, id)

    return deleted


###################################################################################3
@router_indexed.post('/{source_id}/index')
async def index_data(
        source_id: IdType,
        background_tasks: BackgroundTasks,
        db=Depends(get_db),
        searching_inst=Depends(get_searching_instruments),

):
    source = crud_sources.get(db=db, id=source_id)
    if not source:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    data: dict = read_json(source.filepath)
    bible: Bible = get_bible(data)

    background_tasks.add_task(index_data_command_sberbank, bible, searching_inst)

    return Response(status_code=status.HTTP_202_ACCEPTED)


@router_indexed.post('/{source_id}/delete')
async def delete_indexed_data(source_id: Optional[IdType],
                              searching_inst: SearchingEntity = Depends(get_searching_instruments)):
    searching_inst.document_array.clear()
    searching_inst.document_array.summary()

    return Response(status_code=status.HTTP_200_OK)


@router_query.post('/ru/send')
async def send_query(query: str, limit_results: int = 3, searching_instruments=Depends(get_searching_instruments)):
    print(query)
    started = datetime.now()

    answers: List[Result] = query_command_sberbank(query, limit_results, searching_instruments)

    time_processed = datetime.now() - started

    return ResponseDocs(query=query,
                        time_processed=time_processed,
                        results_limit=limit_results,
                        results=answers)

@router_query.post('/en/bbe/send')
async def send_query(query: str, limit_results: int = 3, searching_instruments=Depends(en_search_inst)):
    print(query)
    started = datetime.now()

    answers: List[Result] = en_query(query, limit_results, searching_instruments)

    time_processed = datetime.now() - started

    return ResponseDocs(query=query,
                        time_processed=time_processed,
                        results_limit=limit_results,
                        results=answers)

@router_query.post('/en/kjv/send')
async def send_query(query: str, limit_results: int = 3, searching_instruments=Depends(en_search_inst)):
    print(query)
    started = datetime.now()

    answers: List[Result] = en_query(query, limit_results, searching_instruments)

    time_processed = datetime.now() - started

    return ResponseDocs(query=query,
                        time_processed=time_processed,
                        results_limit=limit_results,
                        results=answers)


@router_indexed.get('/summary')
async def get_summary(searching_instruments:SearchingEntity=Depends(get_searching_instruments)):
    searching_instruments.document_array.summary()

    return {"result":"for testing purposes, see backend console output"}