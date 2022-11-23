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

    for b in bible.Books:
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
        query_filter=models.Filter(
            should=[
                models.FieldCondition(
                    key="text",
                    match=models.MatchValue(
                        value='небо', ## чтобы найти соотвествие с текстом из базы, надо передать поле (стих) полностью
                    ),
                )
            ]
        ),
    )

    print(results)

query_native_with_filters('И отложился Моав от Израиля по смерти Ахава.')

# 3.2 query full-text match



