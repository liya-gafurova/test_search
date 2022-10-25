from transformers import AutoTokenizer, AutoModel

from app.settings import settings

tokenizer_rubert = AutoTokenizer.from_pretrained(settings.MODEL)
model_rubert = AutoModel.from_pretrained(settings.MODEL)

