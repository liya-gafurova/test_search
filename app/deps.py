import secrets
from typing import Generator

import torch
from docarray import DocumentArray
from fastapi import Depends, HTTPException, Header, Security
from fastapi.security import HTTPBasicCredentials, HTTPBasic, APIKeyHeader
from starlette import status
from starlette.status import HTTP_403_FORBIDDEN
from transformers import AutoModel, AutoTokenizer

from app.db.db import SessionLocal
from app.domain.nn import model_sber, tokenizer_sber, sentence_embeds_en
from app.domain.storage import document_array_qdrant, da_qdrand_en_bbe, da_qdrand_en_kjv
from app.settings import settings

security = HTTPBasic()


async def get_db() -> Generator:
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()


class SearchingEntity:
    model: AutoModel = model_sber
    tokenizer: AutoTokenizer = tokenizer_sber
    document_array: DocumentArray = document_array_qdrant

    def get_sentence_embedding(self, sentence: str):
        def mean_pooling(model_output, attention_mask):
            token_embeddings = model_output[0]  # First element of model_output contains all token embeddings
            input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
            sum_embeddings = torch.sum(token_embeddings * input_mask_expanded, 1)
            sum_mask = torch.clamp(input_mask_expanded.sum(1), min=1e-9)
            return sum_embeddings / sum_mask

        encoded_input = self.tokenizer([sentence], padding=True, truncation=True, max_length=24, return_tensors='pt')

        # Compute token embeddings
        with torch.no_grad():
            model_output = self.model(**encoded_input)

        # Perform pooling. In this case, mean pooling
        sentence_embeddings = mean_pooling(model_output, encoded_input['attention_mask'])
        embedding = sentence_embeddings[0].detach().numpy()  # [0] take first index because function is for list[sentence], but we have only one sentence

        return embedding


async def get_searching_instruments() -> SearchingEntity:
    return SearchingEntity()

class EnSearch:
    model = sentence_embeds_en
    da = da_qdrand_en_bbe

    def get_embedding(self, sentence):
        embed = self.model.encode([sentence])

        return embed
async def en_search_inst() -> EnSearch:
    return EnSearch()

class EnKJVSearch:
    model = sentence_embeds_en
    da = da_qdrand_en_kjv


    def get_embedding(self, sentence):
        embed = self.model.encode([sentence])

        return embed
async def en_kjv_search_inst() -> EnKJVSearch:
    return EnKJVSearch()


def check_credentials(credentials: HTTPBasicCredentials = Depends(security)):
    correct_username = secrets.compare_digest(credentials.username, settings.ADMIN_USERNAME)
    correct_password = secrets.compare_digest(credentials.password, settings.ADMIN_PASSWORD)

    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Basic"},
        )

    return credentials.username


API_KEY = "9ab882b1d635e2a7b6bc9169cb6b3f77f82362d11536622c5b5a488eade07188"
API_KEY_NAME = "X-API-KEY"


api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

async def get_api_key(
    api_key_header: str = Security(api_key_header),
):
    if api_key_header == API_KEY:
        return api_key_header
    else:
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN, detail="Could not validate credentials"
        )


