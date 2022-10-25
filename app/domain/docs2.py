from docarray import Document, DocumentArray

from app.domain.nn import model_rubert, tokenizer_rubert
from app.domain.utils import create_dir_if_not_exists, read_json
from app.settings import settings



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

    document_array.embed(model_rubert, collate_fn=collate_fn)

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
    da_query = DocumentArray([Document(text=q)]).embed(model_rubert, collate_fn=collate_fn)

    res = document_array.find(da_query, metric='cosine', limit=1)
    print(q)
    res[0].summary()

    return res[0][0]


if  __name__ == "__main__":
    queries = [
        'в начале бог создал небо и землю',
        'бог назвал твердь небом, было утро и был вечер',
        "только плоти с душею ее, с кровью ее, не ешьте;",
        "И сказал Бог Ною и сынам его с ним:",
        "Он сказал: голос Твой я услышал в раю, и убоялся, потому что я наг, и скрылся",

    ]

    for q in queries:
        answer  = query(q)
        print(f'Answer: {answer.text} -- {answer.scores}')

    # index()