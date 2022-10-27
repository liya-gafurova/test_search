from docarray import Document, DocumentArray

from app.domain.nn import *
from app.domain.utils import create_dir_if_not_exists, read_json
from app.schemas import Bible
from app.settings import settings

def collate_fn(da):
    return tokenizer_sber(da.texts, return_tensors="pt", truncation=True, padding=True)



def index():
    indexed_datadir = create_dir_if_not_exists(settings.INDEXED_DATA_DIR)

    document_array = DocumentArray(
        storage='annlite',
        config={
            'data_path': indexed_datadir,
            'n_dim': 768,
            'metric': 'cosine'
        },
    )

    print(document_array.summary())

    datapath = '/home/lia/PycharmProjects/bible_search/data/VERSES_SMALL_bible_large_20221024232834.json'
    data_json: dict = read_json(datapath)

    for id, text in data_json.items():
        document_array.append(Document(text=text, id=id))

    document_array.embed(model_sber, collate_fn=collate_fn)

    print(document_array.summary())




def query(q: str):
    indexed_datadir = create_dir_if_not_exists(settings.INDEXED_DATA_DIR)

    document_array = DocumentArray(
        storage='annlite',
        config={
            'data_path': indexed_datadir,
            'n_dim': 768
        },
    )

    print(document_array.summary())

    query = Document(text='бог сказал что будет свет')
    da_query = DocumentArray([query]).embed(model_sber, collate_fn=collate_fn)

    res = document_array.find(da_query, metric='cosine', limit=3)
    res[0].summary()


if  __name__ == "__main__":
    queries = [
        'в начале бог создал небо и землю',
        'бог назвал твердь небом, было утро и был вечер',
        "только плоти с душею ее, с кровью ее, не ешьте;",
        "И сказал Бог Ною и сынам его с ним:",
    ]

    for q in queries:
        query(q)