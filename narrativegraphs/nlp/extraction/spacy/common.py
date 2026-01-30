import logging
from abc import abstractmethod
from typing import Generator

import psutil
import spacy
from spacy.tokens import Doc, Span

from narrativegraphs.nlp.extraction.common import Triplet, TripletExtractor
from narrativegraphs.nlp.utils.spacysegmentation import custom_sentencizer  # noqa

_logger = logging.getLogger("narrativegraphs.nlp.extraction")


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


def _ensure_spacy_model(name: str):
    """Ensure spaCy model is available, downloading if necessary."""
    try:
        return spacy.load(name)
    except OSError:
        _logger.info(
            f"First-time setup: downloading spaCy model '{name}'. "
            f"This is a one-time download (~50-500MB depending on model) "
            f"and may take a few minutes..."
        )

        try:
            spacy.cli.download(name)
            return spacy.load(name)
        except Exception as e:
            _logger.error(f"Failed to download model '{name}': {e}")
            raise RuntimeError(
                f"Could not automatically download spaCy model '{name}'.\n"
                f"Please install it manually with:\n"
                f"  python -m spacy download {name}\n"
                f"If you continue to have issues, see: "
                f"https://spacy.io/usage/models"
            ) from e


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
        self.nlp = _ensure_spacy_model(model_name)
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
            batch_size = _calculate_batch_size(texts, n_cpu)
        _logger.info("Using multiple CPU cores.Progress bars may stand still at first.")
        for doc in self.nlp.pipe(texts, n_process=n_cpu, batch_size=batch_size):
            yield self.extract_triplets_from_doc(doc)
