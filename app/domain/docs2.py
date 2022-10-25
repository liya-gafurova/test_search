from docarray import Document, DocumentArray

from app.domain.nn import model, tokenizer
from app.domain.utils import create_dir_if_not_exists, read_json
from app.schemas import Bible
from app.settings import settings

def collate_fn(da):
    return tokenizer(da.texts, return_tensors="pt", truncation=True, padding=True)



def index():
    indexed_datadir = create_dir_if_not_exists(settings.INDEXED_DATA_DIR)

    document_array = DocumentArray(
        storage='qdrant',
        config={
            'collection_name': "lg",
            'host': 'localhost',
            'port': '6333',
            'n_dim': 768,
        },
    )

    document_array.summary()

    datapath = '/home/lia/PycharmProjects/bible_search/data/VERSES_SMALL_bible_large_20221024232834.json'
    data_json: dict = read_json(datapath)

    for id, text in data_json.items():
        document_array.append(Document(text=text, id=id))

    document_array.embed(model, collate_fn=collate_fn)

    print(document_array.summary())




def query(q: str):
    indexed_datadir = create_dir_if_not_exists(settings.INDEXED_DATA_DIR)

    document_array = DocumentArray(
        storage='qdrant',
        config={
            'collection_name': "lg",
            'host': 'localhost',
            'port': '6333',
            'n_dim': 768,
        },
    )
    document_array.summary()
    print('-------------------')


    query = Document(text=q)
    da_query = DocumentArray([Document(text=q)]).embed(model, collate_fn=collate_fn)

    res = document_array.find(da_query,  limit=1)
    print(q)
    res[0].summary()

    return res[0][0, 'text']


if  __name__ == "__main__":
    queries = [
        'в начале бог создал небо и землю',
        'бог назвал твердь небом, было утро и был вечер',
        "только плоти с душею ее, с кровью ее, не ешьте;",
        "И сказал Бог Ною и сынам его с ним:",
    ]

    for q in queries:
        answer  = query(q)
        print(f'Answer: {answer}')

    # index()