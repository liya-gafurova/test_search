"""
можно подключить поиск по ключевым словам:

1. прямое вхождение подстроки

для того, что добавить фильтрацию по подстроке, надо добавить поле payload.text для
непосредсвенного хранения в qdrant
сейчас из-за использования docarray текст не созраняется в payload.text,
но сохраняется payload._serialized в сериализованном
виде (сериализуется целый обьект docarray.Document).

1.1. Чтобы решить эту проблему надо перенести поле Document.text в payload.text
 -- единоразовая переиндексация
 (последующей индексации в случае сохранения docarray оставить текст  в поле,
 название которого отличается от text - например, verse)

1.2. после этой единоразовой переиндексации можно будет делать запросы
через функционал docarray с дополнительным фильтром
  и получить фильтрацию по подстроке


2. контекстный поиск

для полноценного контекстного поиска нужно сделать
индексацию данных с помощью fulltex index

- в качестве базовых данных можно сипользовать данные с пункта 1.1
(послелующая индексация  text -> verse)
- также можно использовать данные, полученные индексацией
данных без использования docarray

"""
import base64
import json
import pickle
from datetime import datetime
from typing import Optional

import torch
from docarray import DocumentArray, Document
from qdrant_client import QdrantClient
from qdrant_client.http.models import models
from transformers import AutoModel, AutoTokenizer

from app.schemas import Bible

IP_ADDR = '192.168.88.223'
COLLECTION_NAME = 'EN_BBE2'
COLLECTION_NAME2 = 'QDRANT_CLIENT'
filepath = '/home/lia/PycharmProjects/bible_search/data/SMALL_bible_large_20221024232834.json'


# class Search:
#     MODEL = 'sberbank-ai/sbert_large_mt_nlu_ru'
#     model = AutoModel.from_pretrained(MODEL)
#     tokenizer = AutoTokenizer.from_pretrained(MODEL)
#
#     def get_embedding(self, sentence):
#         def mean_pooling(model_output, attention_mask):
#             token_embeddings = model_output[0]  # First element of model_output contains all token embeddings
#             input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
#             sum_embeddings = torch.sum(token_embeddings * input_mask_expanded, 1)
#             sum_mask = torch.clamp(input_mask_expanded.sum(1), min=1e-9)
#             return sum_embeddings / sum_mask
#
#         encoded_input = self.tokenizer([sentence], padding=True, truncation=True, max_length=24, return_tensors='pt')
#
#         # Compute token embeddings
#         with torch.no_grad():
#             model_output = self.model(**encoded_input)
#
#         # Perform pooling. In this case, mean pooling
#         sentence_embeddings = mean_pooling(model_output, encoded_input['attention_mask'])
#         embedding = sentence_embeddings[
#             0].detach().numpy()  # [0] take first index because function is for list[sentence], but we have only one sentence
#
#         return embedding


# model = Search()
da = DocumentArray(
    storage='qdrant',
    config={
        'collection_name': COLLECTION_NAME,
        'host': IP_ADDR,
        'port': '6333',
        'n_dim': 1024,
        'columns': {'text': 'str', 'book_id': 'int', 'chapter_id': 'int', 'verse_id': 'int'}
    },
)

client = QdrantClient(host=IP_ADDR, port='6333')

with open(filepath, 'r') as file:
    data_raw = file.read()
    data_dict = json.loads(data_raw)

bible = Bible.parse_raw(data_raw)


def create_semantic_vector(bible):


    start = datetime.now()

    for i, b in enumerate(bible.Books):
        for c in b.Chapters:
            for v in c.Verses:
                document: Document = Document(
                    text=v.Text,
                    verse_id=v.VerseId,
                    chapter_id=c.ChapterId,
                    book_id=b.BookId,
                    embedding=model.get_embedding(v.Text)
                )

                da.append(document)

    finish = datetime.now()
    da.summary()
    print(f'Processing took: {finish-start}')

def decompress_bytes(data: bytes, algorithm: Optional[str] = None) -> bytes:
    if algorithm == 'lz4':
        import lz4.frame

        data = lz4.frame.decompress(data)
    elif algorithm == 'bz2':
        import bz2

        data = bz2.decompress(data)
    elif algorithm == 'lzma':
        import lzma

        data = lzma.decompress(data)
    elif algorithm == 'zlib':
        import zlib

        data = zlib.decompress(data)
    elif algorithm == 'gzip':
        import gzip

        data = gzip.decompress(data)
    return data


def refill_text(bible):
    for i, book in enumerate(bible.Books):
        start = datetime.now()
        results = client.scroll(
            collection_name=COLLECTION_NAME,
            scroll_filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key="book_id",
                        match=models.MatchValue(value=i+1)
                    ),
                ]
            ),
            limit=30000,
            with_payload=True,
        )
        print(f"Verses count: {len(results[0])}")
        finish_response = datetime.now()

        for res in results[0]:
            print(res)
            payload = res.payload
            bts = base64.b64decode(payload['_serialized'])
            bstr = decompress_bytes(bts)
            data = pickle.loads(bstr)

            r = client.set_payload(
                collection_name=COLLECTION_NAME,
                payload={
                    "verse": data.text,
                },
                points=[data.id],
            )
            print(f'After update: {r}')

        finish_update = datetime.now()

        print(f"Book retrieve: {finish_response - start}")
        print(f'Book update: {finish_update - finish_response}')


def get_collection_info():
    info = client.get_collection(collection_name=COLLECTION_NAME)
    print(info)
#
#
# def add_index():
#     # same as full_text_index()
#     info = client.create_payload_index(
#         collection_name=COLLECTION_NAME,
#         field_name="verse",
#         field_schema=models.TextIndexParams(
#             type="text",
#             tokenizer=models.TokenizerType.WORD,
#             min_token_len=2,
#             max_token_len=15,
#             lowercase=True,
#         )
#     )
#     print(info)
#     return info

def query_data_with_text(query: str):
    query_doc = Document(text=query, embedding=model.get_embedding(query))
    query_da = DocumentArray([query_doc])

    results = da.find(query_da, filter=models.Filter(
        should=[
            models.FieldCondition(
                key="verse",
                match=models.MatchText(
                    text='землю',  ## чтобы найти соотвествие с текстом из базы, надо передать поле (стих) полностью
                ),
            )
        ]
    ), metric='cosine', limit=5)

    for r in results[0]:
        print(f"{r.text} -- {r.id} -- {r.scores} -- {r.embedding.shape}")
        print(r.tags)



# create_semantic_vector(bible)
#
# get_collection_info()

# refill_text(bible)

# get_collection_info()


# query_data_with_text('бо созадал небо')

# add_index()

# client.delete_collection(COLLECTION_NAME)

results = client.scroll(
    collection_name=COLLECTION_NAME,
    scroll_filter=models.Filter(
        must=[
            models.FieldCondition(
                key="book_id",
                match=models.MatchValue(value=1)
            ),
            models.FieldCondition(
                key="chapter_id",
                match=models.MatchValue(value=1)
            ),
            models.FieldCondition(
                key="verse_id",
                match=models.MatchValue(value=1)
            ),
        ],
    ),
    limit=10,
    with_payload=True,
    with_vectors=False,
)

print(results)

results = client.scroll(
    collection_name=COLLECTION_NAME,
    scroll_filter=models.Filter(
        must=[
            models.FieldCondition(
                key="verse",
                match=models.MatchText(text='Бог')
            )
        ],
    ),
    limit=10,
    with_payload=True,
    with_vectors=False,
)

print(results)