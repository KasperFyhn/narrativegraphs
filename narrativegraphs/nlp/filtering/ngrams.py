import math
from collections import Counter
from typing import Iterable

import nltk
import spacy

from narrativegraphs.nlp.utils.spacysegmentation import custom_sentencizer  # noqa


def _bigrams(tokens: list[str]):
    return nltk.ngrams(tokens[:-1], 2)


class BigramFilter:
    def __init__(
        self,
        model_name: str = None,
        lowercase: bool = True,
        min_count: int = 3,
        min_pmi: float = -0.5,
    ):
        if model_name is None:
            model_name = "en_core_web_sm"
        self.nlp = spacy.load(model_name, enable=["tokenizer"])
        self._lowercase = lowercase

        self._total_token_count = 0
        self._tokens = Counter()
        self._bigrams = Counter()

        self.min_count = min_count
        self.min_pmi = min_pmi

    def _normalize_token(self, token: str):
        if self._lowercase:
            token = token.lower()
        return token

    def _normalize_bigram(self, bigram: tuple[str, str]):
        return self._normalize_token(bigram[0]), self._normalize_token(bigram[1])

    def _pmi(self, bigram: tuple[str, str]):
        norm_bigram = self._normalize_bigram(bigram)

        return (
            math.log(self._bigrams[norm_bigram])
            + math.log(self._total_token_count)
            - math.log(self._tokens[bigram[0]])
            - math.log(self._tokens[bigram[1]])
        )

    def fit(self, texts: Iterable[str]) -> "BigramFilter":
        for doc in self.nlp.pipe(texts):
            tokens = [t.text for t in doc]
            self._tokens.update(tokens)
            self._bigrams.update(_bigrams(tokens))

        self._total_token_count = sum(self._tokens.values())

        return self

    def passes(self, span: str) -> bool:
        tokens = [self._normalize_token(token.text) for token in self.nlp(span)]
        return all(
            # let unigrams pass
            (len(bigram) == 1 and self._tokens[bigram[0]] >= self.min_count)
            or (
                # check for count and association
                self._bigrams[bigram] >= self.min_count
                and self._pmi(bigram) >= self.min_pmi
            )
            for bigram in _bigrams(tokens)
        )
