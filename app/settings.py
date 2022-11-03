from pydantic import BaseSettings


class Settings(BaseSettings):
    SQLALCHEMY_DATABASE_URI = "sqlite:///./common_db.db"
    SOURCE_FILES_DIR = './data/'
    INDEXED_DATA_DIR = './data/indexed/'
    MODEL = 'sberbank-ai/sbert_large_mt_nlu_ru' # "DeepPavlov/rubert-base-cased"
    EN_MODEL = 'sentence-transformers/all-mpnet-base-v2'
    COLLECTION_NAME = 'bible_large'

    IP_ADDR = '192.168.88.223'

    ADMIN_USERNAME = 'admin'
    ADMIN_PASSWORD = '1234'


settings = Settings()