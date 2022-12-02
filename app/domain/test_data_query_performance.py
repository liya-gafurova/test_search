import asyncio
import datetime
import json
import random
from urllib.parse import urlencode

from aiohttp import ClientSession
import nltk
import requests
from nltk.corpus import brown

# nltk.download("brown")
#
#
# WORDS = brown.words()
# WORDS_COUNT = len(WORDS)
FILEPATH = "/home/lia/PycharmProjects/bible_search/data/test_set.json"
FILEPATH_FILTERING = "/home/lia/PycharmProjects/bible_search/data/test_set_filtering.json"


def generate_random_sentence(word_count: int = 7):
    generated_words = []
    for i in range(word_count):
        random_word_id = random.randint(0, WORDS_COUNT)

        generated_word = WORDS[random_word_id]
        while len(generated_word) <= 1:
            random_word_id = random.randint(0, WORDS_COUNT)
            generated_word = WORDS[random_word_id]

        generated_words.append(generated_word)

    return " ".join(generated_words)


def generate_sentences(sentence_count: int = 1000):
    sentences = []

    for i in range(sentence_count):
        words_in_sentence = random.randint(1, 1)
        sentence = generate_random_sentence(words_in_sentence)
        sentences.append(sentence)

    return sentences


def create_sentences(filepath: str):
    generated = generate_sentences(sentence_count=1000)
    data = {"sentences": generated}

    with open(filepath, "w") as out_file:
        out_file.write(json.dumps(data, ensure_ascii=False))


# create_sentences(FILEPATH)

def get_request_data(sentence):
    param = urlencode(
        {"lang": "en", "translation": "kjv", "query": sentence, "limit": 3}
    )

    url = f"http://localhost:8000/api/v1/queries/query?{param}"

    payload = {}
    headers = {
        "accept": "application/json",
        "X-API-KEY": "9ab882b1d635e2a7b6bc9169cb6b3f77f82362d11536622c5b5a488eade07188",
    }
    return url, headers, payload


async def make_async_request(session, url, headers, data, i):
    print(f"Start request {i}...")
    async with session.get(url, headers=headers, data=data) as resp:
        results = await resp.json()
        print(resp.status)
        print(f"Finish request {i}...")
        return results


def test_queries(data_filepath: str):
    with open(data_filepath, "r") as file:
        data = file.read()
        sentences = json.loads(data)["sentences"]

    start = datetime.datetime.now()

    for sentence in sentences:

        url, headers, payload = get_request_data(sentence)

        response = requests.request("GET", url, headers=headers, data=payload)

        print(response.text)

    finish = datetime.datetime.now()

    print(f"Result, processing took: {finish - start}")


# straight forward -- about 3.20 ]
# TODO add async -- 3.20
# TODO add threads --


# search (semantic -> words in sentence more than 1):

# 1 thread  about 3-5 min
# 25 threads - 1.23
# 12 threads - 1.12
# 6 threads - 1.23
# 2 threads - 1.23
# 1 threads  - 1.23 / 1.36

# singular request - about 0.6 sec


# filtering (filtering = filtering by substring, words in sentence == 1)

# n threads - 20 sec
# singular request - about 0.01 sec

# AFTER run_in_threadpool
# filtering (filtering = filtering by substring, words in sentence == 1)
# n threads - 0.8 sec






async def main():
    with open(FILEPATH, "r") as file:
        data = file.read()
        sentences = json.loads(data)["sentences"]

    async with ClientSession() as session:

        tasks = []
        for i, sentence in enumerate(sentences):
            url, headers, payload = get_request_data(sentence)
            tasks.append(
                asyncio.create_task(
                    make_async_request(session, url, headers, payload, i)
                )
            )

        r = await asyncio.wait(tasks)


if __name__ == "__main__":

    start = datetime.datetime.now()
    results = asyncio.run(main())
    finish = datetime.datetime.now()

    print(f"{finish - start}")
