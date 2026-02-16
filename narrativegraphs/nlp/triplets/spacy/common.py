import logging
from abc import abstractmethod
from typing import Generator

from spacy.tokens import Doc, Span

from narrativegraphs.nlp.common.spacy import (
    calculate_batch_size,
    ensure_spacy_model,
)
from narrativegraphs.nlp.triplets.common import Triplet, TripletExtractor

_logger = logging.getLogger("narrativegraphs.nlp.extraction")


class SpacyTripletExtractor(TripletExtractor):
    """Base class for implementing triplet extraction based on spaCy docs.

    Override `extract_triplets_from_sent` for extracting triplets sentence by sentence.

    Override `extract_triplets_from_doc` for extracting with the full Doc context.

    The `SpanAnnotation` objects of `Triplet` objects can conveniently be created from
    a spaCy `Span` object with `SpanAnnotation.from_span()`.
    """

    def __init__(
        self, model_name: str = None, split_sentence_on_double_line_break: bool = True
    ):
        """
        Args:
            model_name: name of the spaCy model to use
            split_sentence_on_double_line_break: adds extra sentence boundaries on
                double line breaks ("\n\n")
        """
        if model_name is None:
            model_name = "en_core_web_sm"
        self.nlp = ensure_spacy_model(model_name)
        if split_sentence_on_double_line_break:
            self.nlp.add_pipe("custom_sentencizer", before="parser")

    @abstractmethod
    def extract_triplets_from_sent(self, sent: Span) -> list[Triplet]:
        """Extract triplets from a SpaCy sentence.
        Args:
            sent: A SpaCy Span object representing the whole sentence

        Returns:
            extracted triplets
        """
        pass

    def extract_triplets_from_doc(self, doc: Doc) -> list[Triplet]:
        """Extract triplets from a Doc
        Args:
            doc: A SpaCy Doc object

        Returns:
            extracted triplets
        """
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
        self, texts: list[str], n_cpu: int = 1, batch_size: int = None
    ) -> Generator[list[Triplet], None, None]:
        if batch_size is None:
            batch_size = calculate_batch_size(texts, n_cpu)
        if n_cpu > 1:
            _logger.info(
                "Using multiple CPU cores.Progress bars may stand still at first."
            )
        for doc in self.nlp.pipe(texts, n_process=n_cpu, batch_size=batch_size):
            yield self.extract_triplets_from_doc(doc)
