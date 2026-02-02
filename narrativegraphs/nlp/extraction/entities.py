from abc import ABC, abstractmethod
from typing import Generator, Iterable

from narrativegraphs.nlp.extraction.common import SpanAnnotation


class EntityExtractor(ABC):
    """
    Abstract base class for entity extraction algorithms.

    Entities are instantiated as SpanAnnotation objects representing
    named entities, noun chunks, or other spans of interest in the text.
    """

    @abstractmethod
    def extract(self, text: str) -> list[SpanAnnotation]:
        """Single document extraction.

        Args:
            text: a raw text string

        Returns:
            extracted entities as SpanAnnotation objects
        """
        pass

    def batch_extract(
        self, texts: Iterable[str], n_cpu: int = 1, **kwargs
    ) -> Generator[list[SpanAnnotation], None, None]:
        """Multiple-document extraction.

        Args:
            texts: an iterable of raw text strings; may be a generator, so be mindful
                of consuming items
            n_cpu: number of CPUs to use
            **kwargs: other keyword arguments for your own class

        Returns:
            should yield entities per text in the same order as texts iterable
        """
        for text in texts:
            yield self.extract(text)
