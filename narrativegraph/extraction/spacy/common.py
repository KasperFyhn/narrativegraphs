from abc import abstractmethod
from typing import Generator

import spacy
from spacy.tokens import Doc, Span

from narrativegraph.extraction.common import TripletExtractor, Triplet


class SpacyTripletExtractor(TripletExtractor):

    def __init__(self, model_name: str = None):
        if model_name is None:
            model_name = "en_core_web_sm"
        self.nlp = spacy.load(model_name)
        pass

    @abstractmethod
    def extract_triplets_from_sent(self, sent: Span) -> list[Triplet]:
        pass

    def extract_triplets_from_doc(self, doc: Doc) -> list[Triplet]:
        triplets = []
        for sent in doc.sents:
            sent_triplets = self.extract_triplets_from_sent(sent)
            if sent_triplets is not None:
                triplets.extend(sent_triplets)
        return triplets

    def extract(self, text: str) -> list[Triplet]:
        text = self.nlp(text)
        return self.extract_triplets_from_doc(text)

    def batch_extract(self, texts: list[str], n_cpu: int = -1, **kwargs) \
            -> Generator[list[Triplet], None, None]:
        for doc in self.nlp.pipe(texts, n_process=n_cpu, batch_size=250):
            yield self.extract_triplets_from_doc(doc)
