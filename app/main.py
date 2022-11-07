import uvicorn
from fastapi import FastAPI, Depends

from app import log
from app.db.base_class import Base
from app.db.db import engine
from app.deps import check_credentials
from app.routers import router_source, router_query, router_indexed

logger = log.get_logger(__name__)

app = FastAPI()

app.include_router(router_source, prefix='/source', tags=['Source Texts'], dependencies=[Depends(check_credentials)])
app.include_router(router_query, prefix='/query', tags=['Queries'])
app.include_router(router_indexed, prefix='/indexed', tags=['Indexed data'], dependencies=[Depends(check_credentials)])


@app.on_event('startup')
async def start_db():
    Base.metadata.create_all(bind=engine)
    logger.info(f"App started.")


if __name__  == "__main__":
    uvicorn.run('main:app', port=8088, log_level='info')