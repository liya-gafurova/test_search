from transformers import AutoTokenizer, AutoModel

from app.settings import settings

tokenizer_sber = AutoTokenizer.from_pretrained(settings.MODEL)
model_sber = AutoModel.from_pretrained(settings.MODEL)

