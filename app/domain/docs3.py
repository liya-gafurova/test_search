import torch
from docarray import DocumentArray, Document

from transformers import AutoTokenizer, AutoModel
import torch
#Load AutoModel from huggingface model repository


def main():
    sstokenizer = AutoTokenizer.from_pretrained('sberbank-ai/sbert_large_mt_nlu_ru')
    ssmodel = AutoModel.from_pretrained('sberbank-ai/sbert_large_mt_nlu_ru')

    def get_sentence_embedding(sentence: str):

        def mean_pooling(model_output, attention_mask):
            token_embeddings = model_output[0]  # First element of model_output contains all token embeddings
            input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
            sum_embeddings = torch.sum(token_embeddings * input_mask_expanded, 1)
            sum_mask = torch.clamp(input_mask_expanded.sum(1), min=1e-9)
            return sum_embeddings / sum_mask

        encoded_input = sstokenizer([sentence], padding=True, truncation=True, max_length=24, return_tensors='pt')

        # Compute token embeddings
        with torch.no_grad():
            model_output = ssmodel(**encoded_input)

        # Perform pooling. In this case, mean pooling
        sentence_embeddings = mean_pooling(model_output, encoded_input['attention_mask'])
        embedding = sentence_embeddings[
            0].detach().numpy()  # [0] take first index because function is for list[sentence], but we have only one sentence

        return embedding

    data = {}

    ### INDEX
    da = DocumentArray()

    for id, text in data.items():
        embeddings = get_sentence_embedding([text])

        print(embeddings.shape)

        doc = Document(text=text, id=id, embedding=embeddings)

        da.append(doc)

    da.summary()

    ### QUERY

    query = "Земля же была безвидна и пуста, и тьма над бездною, и Дух Божий носился над водою."

    embedding = get_sentence_embedding(query)

    query_doc = Document(text=query, embedding=embedding)

    da_query = DocumentArray([query_doc])

    res = da.find(da_query, metric='cosine', limit=3)

    for r in res[0]:
        print(f"{r.text} -- {r.id} -- {r.scores} -- {r.embedding.shape}")