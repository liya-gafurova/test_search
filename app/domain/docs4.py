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


class EnSearch:
    model = SentenceTransformer(settings.EN_MODEL)

    def get_embedding(self, sentence):
        embed = self.model.encode([sentence])

        return embed

search_inst = EnSearch()

def index_en_data(filepath):

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

                da_qdrand_en_kjv.append(doc)

        if i > 0: break

    finish = datetime.now()
    print(f"Time indexed: {finish - start}")

    da_qdrand_en_kjv.summary()

def query(q: str):
    q_doc = Document(
        text=q,
        embedding=search_inst.get_embedding(q)
    )
    q_da = DocumentArray([q_doc])

    res = da_qdrand_en_kjv.find(q_da, metric='cosine', limit=3)

    for r in res[0]:
        print(f"{r.text} -- {r.id} -- {r.tags} -- {r.scores['cosine_similarity'].value} -- {r.embedding.shape}")


path = '/home/lia/PycharmProjects/bible_search/data/en_kjv_202211310313.json'
#
index_en_data(path)

# query('god created heaven and earth')

