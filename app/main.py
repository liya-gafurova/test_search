import uvicorn
from fastapi import FastAPI

from app.db.base_class import Base
from app.db.db import engine
from app.routers import router_source, router_query, router_indexed

app = FastAPI()

app.include_router(router_source, prefix='/source', tags=['Source Texts'])
app.include_router(router_query, prefix='/query', tags=['Queries'])
app.include_router(router_indexed, prefix='/indexed', tags=['Indexed data'])


@app.on_event('startup')
async def start_db():
    Base.metadata.create_all(bind=engine)



if __name__  == "__main__":
    uvicorn.run('main:app', port=8088, log_level='info')