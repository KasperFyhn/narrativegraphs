from abc import abstractmethod
from typing import Generator

import psutil
import spacy
from spacy import Language
from spacy.tokens import Doc, Span

from narrativegraph.nlp.extraction.common import TripletExtractor, Triplet


def _calculate_batch_size(texts: list[str], n_cpu: int = -1) -> int:
    """Simple heuristic-based batch size calculation."""
    if not texts:
        raise ValueError("No texts provided.")

    # Calculate average text length
    avg_length = sum(len(text) for text in texts) / len(texts)

    # Determine CPU count
    actual_cpu_count = (
        psutil.cpu_count() if n_cpu == -1 else min(n_cpu, psutil.cpu_count())
    )

    # Base calculation: inverse relationship with text length
    if avg_length < 100:
        base_size = 1000
    elif avg_length < 500:
        base_size = 500
    elif avg_length < 2000:
        base_size = 200
    elif avg_length < 5000:
        base_size = 100
    else:
        base_size = 50

    # Scale by CPU count (more CPUs can handle larger batches)
    scaled_size = base_size * max(1, actual_cpu_count // 4)

    # Apply bounds
    return max(10, min(scaled_size, 2000))


@Language.component("custom_sentencizer")
def custom_sentencizer(doc):
    for i, token in enumerate(doc[:-1]):
        if token.text == "\n\n":
            doc[i + 1].is_sent_start = True

    return doc


class SpacyTripletExtractor(TripletExtractor):

    def __init__(self, model_name: str = None, split_sentence_on_double_line_break: bool = True):
        if model_name is None:
            model_name = "en_core_web_sm"
        self.nlp = spacy.load(model_name)
        if split_sentence_on_double_line_break:
            self.nlp.add_pipe(
                "custom_sentencizer", before="parser"
            )
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

    def batch_extract(
        self, texts: list[str], n_cpu: int = -1, batch_size: int = None
    ) -> Generator[list[Triplet], None, None]:
        if batch_size is None:
            batch_size = _calculate_batch_size(texts, n_cpu)
        for doc in self.nlp.pipe(texts, n_process=n_cpu, batch_size=batch_size):
            yield self.extract_triplets_from_doc(doc)
