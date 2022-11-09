import uuid
from datetime import datetime

import torch
import librosa
from transformers import Wav2Vec2ForCTC, Wav2Vec2Processor

LANG_ID = "ru"
MODEL_ID = "jonatasgrosman/wav2vec2-xls-r-1b-russian"
MODEL_ID2 = 'jonatasgrosman/wav2vec2-large-xlsr-53-russian'
MODEL_ID3 = 'bond005/wav2vec2-large-ru-golos'
model_ids = [MODEL_ID, MODEL_ID2, MODEL_ID3]
SAMPLES = 10

models, processors = [], []
for model_id in model_ids:
    pass

processor = Wav2Vec2Processor.from_pretrained(MODEL_ID)
model = Wav2Vec2ForCTC.from_pretrained(MODEL_ID)


files = ['/home/lia/PycharmProjects/bible_search/data/ru_audio/file1.wav',
         '/home/lia/PycharmProjects/bible_search/data/ru_audio/file2.wav',
         '/home/lia/PycharmProjects/bible_search/data/ru_audio/file3.wav',
         '/home/lia/PycharmProjects/bible_search/data/ru_audio/file4.wav',
         '/home/lia/PycharmProjects/bible_search/data/ru_audio/file5.wav',
         '/home/lia/PycharmProjects/bible_search/data/ru_audio/file6.wav',
         '/home/lia/PycharmProjects/bible_search/data/ru_audio/file7.wav']
texts = ["В начале сотворил Бог небо и землю.",
         "И сказал Бог: да будет свет. И сталсвет." ,
         "И увидел Бог свет, что он хорош, и отделил Бог свет от тьмы.",
         'Авраам родил Исаака;',
         'Исаак родил Иакова;',
         'Иаков родил Иуду и братьев его',
         'и Мелхиседек, царь Салимский, вынес хлеб и вино, — он был священник Бога Всевышнего ']

test_dataset = []

for path, text in zip(files, texts):
  data = {'id': uuid.uuid4().hex, 'path': path, 'text': text}
  speech_array, sampling_rate = librosa.load(path, sr=16_000)
  data['speech'] = speech_array

  test_dataset.append(data)




print(f'Model name: {model.name_or_path}', end='\n\n')
for f in [test_dataset[-1]]:
    start = datetime.now()
    inputs = processor(f['speech'], sampling_rate=16_000, return_tensors="pt", padding=True)

    with torch.no_grad():
        logits = model(inputs.input_values, attention_mask=inputs.attention_mask).logits

    predicted_ids = torch.argmax(logits, dim=-1)
    predicted_sentences = processor.batch_decode(predicted_ids)

    finish = datetime.now()

    print(f'Source: {f["text"]}')
    print(f'Predicted: {predicted_sentences[0]}')
    print(finish - start)
    print('------------------------------------')