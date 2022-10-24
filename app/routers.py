from fastapi import APIRouter, UploadFile, File

from app.schemas import IdType

router_source = APIRouter()
router_query = APIRouter()


@router_source.post('/delete')
async def delete_source_data(id: IdType):
    pass


@router_source.post('/upload')
async def upload_source_data(file: UploadFile = File(...)):
    pass


@router_query.post('/send')
async def send_query(query: str):
    pass
