from typing import Optional

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
