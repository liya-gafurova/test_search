from transformers import AutoTokenizer, AutoModel
from sentence_transformers import SentenceTransformer


from app.settings import settings

tokenizer_sber = AutoTokenizer.from_pretrained(settings.MODEL)
model_sber = AutoModel.from_pretrained(settings.MODEL)

sentence_embeds_en = SentenceTransformer(settings.EN_MODEL)
