from docarray import DocumentArray

from app.settings import settings

document_array_qdrant = DocumentArray(
        storage='qdrant',
        config={
            'collection_name': settings.COLLECTION_NAME,
            'host': settings.IP_ADDR,
            'port': '6333',
            'n_dim': 1024,
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
