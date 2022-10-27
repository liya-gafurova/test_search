from typing import Generator

import torch
from docarray import DocumentArray
from transformers import AutoModel, AutoTokenizer

from app.db.db import SessionLocal
from app.domain.nn import model_sber, tokenizer_sber
from app.domain.storage import document_array_qdrant


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
