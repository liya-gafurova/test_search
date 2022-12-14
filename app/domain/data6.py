import base64
import json
import os
import pickle
from typing import Optional

import torch
from docarray import DocumentArray, Document
from qdrant_client import QdrantClient
from qdrant_client.models import models
from transformers import AutoTokenizer, AutoModel

from app.schemas import Bible

"""
переиндексация не получится, так как поле текст не хранится в qdrant в прямом виде
text хоранится в поле обьекта docarray.Document, который в свою очередь хранится в сериализованном
виде (pickle) в payload поле qdrant
"""
# https://github.com/docarray/docarray/issues/612 -- "Note, this is not real text search, this is text based filtering."
# https://blog.qdrant.tech/qdrant-introduces-full-text-filters-and-indexes-9a032fcb5fa
IP_ADDR = '192.168.88.223'
COLLECTION_NAME = 'EN_BBE2'
COLLECTION_NAME2 = 'QDRANT_CLIENT'

class Search:
    MODEL = 'sberbank-ai/sbert_large_mt_nlu_ru'
    model = AutoModel.from_pretrained(MODEL)
    tokenizer = AutoTokenizer.from_pretrained(MODEL)

    def get_embedding(self, sentence):
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
        embedding = sentence_embeddings[
            0].detach().numpy()  # [0] take first index because function is for list[sentence], but we have only one sentence

        return embedding


model = Search()
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

# 1  create small vector index
def create_semantic_vector(filepath):
    with open(filepath, 'r') as file:
        data_raw = file.read()
        data_dict = json.loads(data_raw)

    bible = Bible.parse_raw(data_raw)

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
        if i> 1: break

    da.summary()

# create_semantic_vector('/home/lia/PycharmProjects/bible_search/data/SMALL_bible_large_20221024232834.json')

# create index with qdrant_client

def index_with_client(filepath):
    collection =  client.recreate_collection(
        collection_name=COLLECTION_NAME2,
        vectors_config=models.VectorParams(size=1024, distance=models.Distance.COSINE),
    )

    with open(filepath, 'r') as file:
        data_raw = file.read()
        data_dict = json.loads(data_raw)

    bible = Bible.parse_raw(data_raw)

    for i, b in enumerate(bible.Books):
        for c in b.Chapters:
            for v in c.Verses:
                vector = model.get_embedding(v.Text)
                client.upsert(
                    collection_name=COLLECTION_NAME2,
                    points=[
                        models.PointStruct(
                            id = os.urandom(16).hex(),
                            payload={
                                "book_id": b.BookId,
                                "chapter_id": c.ChapterId,
                                "verse_id": v.VerseId,
                                'text': v.Text
                            },
                            vector=vector.tolist(),
                        ),
                    ]
                )
        if i >= 2:
            break

    info = client.get_collection(COLLECTION_NAME2)
    print(info)

# index_with_client('/home/lia/PycharmProjects/bible_search/data/SMALL_bible_large_20221024232834.json')


# 2 add full text index



# 3 query

# 3.1 query semantic

def query_data(query: str):
    query_doc = Document(text = query, embedding=model.get_embedding(query))
    query_da = DocumentArray([query_doc])

    results = da.find(query_da, metric='cosine', limit=3)

    for r in results[0]:
        print(f"{r.text} -- {r.id} -- {r.scores} -- {r.embedding.shape}")
        print(r.tags)

# query_data('Бог создал небо')




# 3.2  query with qdrant_client
def query_native(query, client):

    query_vector = model.get_embedding(query)

    results = client.search(
        collection_name=COLLECTION_NAME,
        query_vector=query_vector,
        with_payload=True,
    )

    print(results)

# query_native('Бог создал небо', client)


# 3.3 query with simple filters qdrant_clients

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

def from_bytes( data: bytes,
        protocol: str = 'pickle',
        compress: Optional[str] = None,):

    bstr = decompress_bytes(data,)
    if protocol == 'pickle':
        return pickle.loads(bstr)

    else:
        raise ValueError(
            f'protocol={protocol} is not supported. Can be only `protobuf` or pickle protocols 0-5.'
        )

def query_native_with_filters(query):
    query_vector = model.get_embedding(query)

    results = client.search(
        collection_name = COLLECTION_NAME2,
        query_vector=query_vector,
        limit=100,
        query_filter=models.Filter(
            should=[
                models.FieldCondition(
                    key="text",
                    match=models.MatchText(
                        text = query, ## чтобы найти соотвествие с текстом из базы, надо передать поле (стих) полностью
                    ),
                )
            ]
        ),
    )

    print(results)

# query_native_with_filters('Богу')

# 3.4 query and add full text index

def full_text_index():
    info = client.create_payload_index(
        collection_name=COLLECTION_NAME2,
        field_name="text",
        field_schema=models.TextIndexParams(
            type="text",
            tokenizer=models.TokenizerType.WORD,
            min_token_len=2,
            max_token_len=15,
            lowercase=True,
        )
    )
    print(info)
    return info
def test(query):
    query_vector = model.get_embedding(query)

    results = client.search(
        collection_name=COLLECTION_NAME2,
        query_vector=query_vector,
        limit=100,
        query_filter=models.Filter(
            should=[
                models.FieldCondition(
                    key="text",
                    match=models.MatchText(
                        text='Бог',  ## чтобы найти соотвествие с текстом из базы, надо передать поле (стих) полностью
                    ),
                )
            ]
        ),
    )

    print(results)

# full_text_index()
# test('небо и земля')


# for query in ['Богу', "Моисей", "Бог сотворил небо и землю"]:
#     query_native_with_filters(query)
#     test(query)
#


###
# Reindex Docarray index
###
def refill_text():
    results = client.scroll(
        collection_name=COLLECTION_NAME,
        scroll_filter=models.Filter(
            must=[
                models.FieldCondition(
                    key="book_id",
                    match=models.MatchValue(value=1)
                ),
            ]
        ),
        limit=1000,
        with_payload=True,
    )

    for res in results[0]:
        print(res)
        payload = res.payload
        bts = base64.b64decode(payload['_serialized'])
        bstr = decompress_bytes(bts)
        data  = pickle.loads(bstr)

        client.set_payload(
            collection_name=COLLECTION_NAME,
            payload={
                "text": data.text,
            },
            points=[data.id],
        )

def add_index():
    # same as full_text_index()
    info = client.create_payload_index(
        collection_name=COLLECTION_NAME,
        field_name="text",
        field_schema=models.TextIndexParams(
            type="text",
            tokenizer=models.TokenizerType.WORD,
            min_token_len=2,
            max_token_len=15,
            lowercase=True,
        )
    )
    print(info)
    return info

def query_data_with_text(query: str):
    query_doc = Document(text = query, embedding=model.get_embedding(query))
    query_da = DocumentArray([query_doc])

    results = da.find(query_da, filter=models.Filter(
            should=[
                models.FieldCondition(
                    key="text",
                    match=models.MatchText(
                        text = 'бог земля', ## чтобы найти соотвествие с текстом из базы, надо передать поле (стих) полностью
                    ),
                )
            ]
        ), metric='cosine', limit=5)

    for r in results[0]:
        print(f"{r.text} -- {r.id} -- {r.scores} -- {r.embedding.shape}")
        print(r.tags)
# add_index()

query_data_with_text("Бог сотворил небо и землю")

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