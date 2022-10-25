from pydantic import BaseSettings


class Settings(BaseSettings):
    SQLALCHEMY_DATABASE_URI = "sqlite:///./common_db.db"
    SOURCE_FILES_DIR = './data/'
    INDEXED_DATA_DIR = './data/indexed/'
    MODEL = "DeepPavlov/rubert-base-cased"
    COLLECTION_NAME = 'bible'

    IP_ADDR = '192.168.88.223'


settings = Settings()