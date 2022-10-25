from transformers import AutoTokenizer, AutoModel

from app.settings import settings

tokenizer = AutoTokenizer.from_pretrained(settings.MODEL)
model = AutoModel.from_pretrained(settings.MODEL)

