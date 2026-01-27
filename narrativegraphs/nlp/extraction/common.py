from abc import ABC, abstractmethod
from typing import Generator, Iterable, Optional

from pydantic import BaseModel, ConfigDict
from spacy.tokens import Span, Token


class SpanAnnotation(BaseModel):
    model_config = ConfigDict(frozen=True)

    text: str
    start_char: int
    end_char: int
    normalized_text: Optional[str] = None

    @classmethod
    def from_span(cls, span: Span | Token) -> "SpanAnnotation":
        start = span.start_char if isinstance(span, Span) else span.idx
        end = span.end_char if isinstance(span, Span) else span.idx + len(span.text)
        return cls(
            text=span.text,
            normalized_text=span.lemma_,
            start_char=start,
            end_char=end,
        )


class Triplet(BaseModel):
    subj: SpanAnnotation
    pred: SpanAnnotation
    obj: SpanAnnotation


class Tuplet(BaseModel):
    entity_one: SpanAnnotation
    entity_two: SpanAnnotation


class TripletExtractor(ABC):
    """
    Abstract base class for triplet extraction algorithms.

    Triplets are instantiated as Triplet objects that consist of SpanAnnotation objects.

    Thus, to create a Triplet, you create the
    """

    @abstractmethod
    def extract(self, text: str) -> list[Triplet]:
        """Single document extraction
        Args:
            text: a raw text string

        Returns:
            extracted triplets
        """
        pass

    def batch_extract(
        self, texts: Iterable[str], n_cpu: int = 1, **kwargs
    ) -> Generator[list[Triplet], None, None]:
        """Multiple-document extraction
        Args:
            texts: an iterable of raw text strings; may be a generator, so be mindful
                of consuming items
            n_cpu: number of CPUs to use
            **kwargs: other keyword arguments for your own class

        Returns:
            should yield triplets per text in the same order as texts iterable

        """
        for text in texts:
            yield self.extract(text)
