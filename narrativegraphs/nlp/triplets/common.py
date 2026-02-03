from abc import ABC, abstractmethod
from typing import Generator, Iterable

from pydantic import BaseModel

from narrativegraphs.nlp.common.annotation import SpanAnnotation


class Triplet(BaseModel):
    subj: SpanAnnotation
    pred: SpanAnnotation
    obj: SpanAnnotation


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
