from abc import ABC, abstractmethod
from typing import Generator, Iterable, Optional

from pydantic import BaseModel
from spacy.tokens import Span, Token


class SpanAnnotation(BaseModel):
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
    entity_one_extra_mentions: list[SpanAnnotation] = []
    entity_two_extra_mentions: list[SpanAnnotation] = []

    def combine(self, other: "Tuplet") -> "Tuplet":
        if (
            self.entity_one.text == other.entity_one.text
            and self.entity_two.text == other.entity_two.text
        ):
            self.entity_one_extra_mentions.append(other.entity_one)
            self.entity_two_extra_mentions.append(other.entity_two)
        elif (
            self.entity_one.text == other.entity_two.text
            and self.entity_two.text == other.entity_one.text
        ):
            self.entity_two_extra_mentions.append(other.entity_one)
            self.entity_one_extra_mentions.append(other.entity_two)
        else:
            raise ValueError("Tuplet entities must have same text")
        return self

    @property
    def frequency(self) -> int:
        entity_one_mentions = 1 + len(self.entity_one_extra_mentions)
        entity_two_mentions = 1 + len(self.entity_two_extra_mentions)
        return entity_one_mentions * entity_two_mentions


class TripletExtractor(ABC):
    @abstractmethod
    def extract(self, text: str) -> list[Triplet]:
        pass

    def batch_extract(
        self, texts: Iterable[str], n_cpu: int = 1, **kwargs
    ) -> Generator[list[Triplet], None, None]:
        for text in texts:
            yield self.extract(text)
