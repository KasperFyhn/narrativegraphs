from abc import ABC, abstractmethod
from typing import Generator, Iterable, Optional

from pydantic import BaseModel, ConfigDict

from narrativegraphs.nlp.common.annotation import AnnotationContext, SpanAnnotation


class Triplet(BaseModel):
    model_config = ConfigDict(frozen=True)

    subj: SpanAnnotation
    pred: SpanAnnotation
    obj: SpanAnnotation
    context: Optional[AnnotationContext] = None


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

    def batch_extract_unordered(
        self, texts: Iterable[str], n_cpu: int = 1, **kwargs
    ) -> Generator[tuple[int, list[Triplet]], None, None]:
        """Multiple-document extraction where results may arrive out of order.

        Each document's triplets are yielded together with that document's
        position in `texts`, so callers can attribute results without relying
        on the order they come back in.

        Override this when the backend finishes documents out of order — as an
        LLM backend does — so that results can be handled the moment they land
        instead of being held back for documents that are still running. The
        default implementation delegates to `batch_extract` and is therefore
        ordered, which is a valid special case.

        Args:
            texts: an iterable of raw text strings; may be a generator, so be
                mindful of consuming items
            n_cpu: number of CPUs to use
            **kwargs: other keyword arguments for your own class

        Returns:
            should yield an (index, triplets) pair per text, in any order
        """
        for index, triplets in enumerate(
            self.batch_extract(texts, n_cpu=n_cpu, **kwargs)
        ):
            yield index, triplets
