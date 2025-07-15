from abc import ABC, abstractmethod
from typing import NamedTuple, Generator, Iterable, Optional

from spacy.tokens import Span, Token


class TripletPart(NamedTuple):
    text: str
    start_char: int
    end_char: int
    normalized_text: Optional[str] = None

    @classmethod
    def from_span(cls, span: Span | Token) -> "TripletPart":
        start = span.start_char if isinstance(span, Span) else span.idx
        end = span.end_char if isinstance(span, Span) else span.idx + len(span.text)
        return cls(
            text=span.text,
            normalized_text=span.lemma_,
            start_char=start,
            end_char=end,
        )


class Triplet(NamedTuple):
    subj: TripletPart
    pred: TripletPart
    obj: TripletPart



class TripletExtractor(ABC):
    @abstractmethod
    def extract(self, text: str) -> list[Triplet]:
        pass

    def batch_extract(self, texts: Iterable[str], **kwargs) \
            -> Generator[list[Triplet], None, None]:
        for text in texts:
            yield self.extract(text)
