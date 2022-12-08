import random

from deep_translator import GoogleTranslator

# ru -> de -> en -> pl -> es -> ro -> ru

d = [
     "Am Anfang schuf Gott Himmel und Erde.",
    "Und die Erde war wüst und leer, und es war finster auf der Tiefe; und der Geist Gottes schwebete auf dem Wasser.",
    "Und Gott sprach: Es werde Licht! Und es ward Licht.",
    "Und Gott sah, daß das Licht gut war. Da schied Gott das Licht von der Finsternis",
    "und nannte das Licht Tag und die Finsternis Nacht. Da ward aus Abend und Morgen der erste Tag.",
    "Und Gott sprach: Es werde eine Feste zwischen den Wassern, und die sei ein Unterschied zwischen den Wassern.",
"Da machte Gott die Feste und schied das Wasser unter der Feste von dem Wasser über der Feste. Und es geschah also.",
"Und Gott nannte die Feste Himmel. Da ward aus Abend und Morgen der andere Tag.",
"Und Gott sprach: Es sammle sich das Wasser unter dem Himmel an sondere Örter, daß man das Trockene sehe. Und es geschah also.",
"Und Gott nannte das Trockene Erde, und die Sammlung der Wasser nannte er Meer. Und Gott sah, daß es gut war.",

]


from py_openthesaurus import OpenThesaurus

from germalemma import GermaLemma

lemmatizer = GermaLemma()


def get_syn(word: str):
    open_thesaurus = OpenThesaurus(word=word)

    synonyms = open_thesaurus.get_synonyms()
    if not synonyms:
        return word

    return random.choice(synonyms)

import spacy
nlp =  spacy.load('en_core_web_sm')



doc = nlp(d[0])
for tk in doc:
    print(tk.text, tk.tag_, tk.pos_)





for l in d:
    print(l)
    words = l.split()


    print('*'*50)
