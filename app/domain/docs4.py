from datetime import datetime

from docarray import Document, DocumentArray
from sentence_transformers import SentenceTransformer

from app.domain.utils import read_json
from app.settings import settings

da_qdrand_en_kjv = DocumentArray(
    storage='qdrant',
    config={
        'collection_name': 'EN_KJV',
        'host': settings.IP_ADDR,
        'port': '6333',
        'n_dim': 768,
        'columns': {'text': 'str', 'book_id': 'int', 'chapter_id': 'int', 'verse_id': 'int'}
    },
)

da_qdrand_en_bbe = DocumentArray(
    storage='qdrant',
    config={
        'collection_name': 'EN_BBE',
        'host': settings.IP_ADDR,
        'port': '6333',
        'n_dim': 768,
        'columns': {'text': 'str', 'book_id': 'int', 'chapter_id': 'int', 'verse_id': 'int'}
    },
)



class EnSearch:
    model = SentenceTransformer(settings.EN_MODEL)

    def get_embedding(self, sentence):
        embed = self.model.encode([sentence])

        return embed

search_inst = EnSearch()

def index_en_data(filepath, qdrant):

    data = read_json(filepath)

    start = datetime.now()

    for i, book in enumerate(data):
        for j, chapter in enumerate(book['chapters']):
            for k, verse in enumerate(chapter):

                doc = Document(
                    text = verse,
                    verse_id=k,
                    chapter_id = j,
                    book_id = i,
                    embedding=search_inst.get_embedding(verse)
                )

                qdrant.append(doc)


    finish = datetime.now()
    print(f"Time indexed: {finish - start}")

    qdrant.summary()

def query(q: str, qdrant):
    q_doc = Document(
        text=q,
        embedding=search_inst.get_embedding(q)
    )
    q_da = DocumentArray([q_doc])

    res = qdrant.find(q_da, metric='cosine', limit=3)

    for r in res[0]:
        print(f"{r.text} -- {r.id} -- {r.tags} -- {r.scores['cosine_similarity'].value} -- {r.embedding.shape}")


path1 = '/home/lia/PycharmProjects/bible_search/data/en_kjv_202211310313.json'
path2 = '/home/lia/PycharmProjects/bible_search/data/en_bbe_2022113103552.json'
paths = [path1, path2]
#

qdrants = [da_qdrand_en_kjv, da_qdrand_en_bbe]

for path, qd in zip(paths, qdrants):
    index_en_data(path, qd)

    print(f'Done {path}')




# query('god created heaven and earth')

