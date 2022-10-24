import uvicorn
from fastapi import FastAPI

from app.routers import router_source, router_query

app = FastAPI()

app.include_router(router_source, prefix='/source', tags=['Source Texts'])
app.include_router(router_query, prefix='/query', tags=['Queries'])

if __name__  == "__main__":
    uvicorn.run('main:app', port=8088, log_level='info')