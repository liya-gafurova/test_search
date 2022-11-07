from pydantic import BaseSettings


class Settings(BaseSettings):
    SQLALCHEMY_DATABASE_URI = "sqlite:///./common_db.db"
    SOURCE_FILES_DIR = './data/'
    INDEXED_DATA_DIR = './data/indexed/'
    MODEL = 'sberbank-ai/sbert_large_mt_nlu_ru' # "DeepPavlov/rubert-base-cased"
    EN_MODEL = 'sentence-transformers/all-mpnet-base-v2'
    COLLECTION_NAME = 'bible_large'

    IP_ADDR: str

    ADMIN_USERNAME: str
    ADMIN_PASSWORD: str

    class Config:
        env_file='.env'


settings = Settings()