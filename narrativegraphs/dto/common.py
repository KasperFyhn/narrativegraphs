from datetime import date
from typing import Optional, TypeVar

from fastapi_camelcase import CamelModel

from narrativegraphs.db.documents import AnnotationBackedTextStatsMixin


class BaseDetails(CamelModel):
    id: int
    categories: Optional[dict[str, list[str]]]


class TextOccurrenceStats(CamelModel):
    frequency: int
    doc_frequency: int
    adjusted_tf_idf: float
    first_occurrence: Optional[date] = None
    last_occurrence: Optional[date] = None
    doc_ids: set[int]

    @classmethod
    def from_mixin(cls, orm: AnnotationBackedTextStatsMixin):
        return cls(
            frequency=orm.frequency,
            doc_frequency=orm.doc_frequency,
            adjusted_tf_idf=orm.adjusted_tf_idf,
            first_occurrence=orm.first_occurrence,
            last_occurrence=orm.last_occurrence,
            doc_ids=orm.doc_ids,
        )


class TextOccurrence(BaseDetails):
    stats: TextOccurrenceStats


class LabeledTextOccurrence(TextOccurrence):
    label: str
    alt_labels: Optional[list[str]] = None


_TextContext = TypeVar("_TextContext", bound="TextContext")


class TextContext(CamelModel):
    doc_id: int
    text: str
    doc_offset: int = 0

    def overlaps(self, other: _TextContext) -> bool:
        if self.doc_id != other.doc_id:
            return False
        first = min(self, other, key=lambda tc: tc.doc_offset)
        second = self if first is other else other
        first_end_char = first.doc_offset + len(first.text)
        return first_end_char > second.doc_offset

    def combine(self, other: _TextContext) -> _TextContext:
        if not self.overlaps(other):
            raise ValueError("Cannot combine non-overlapping TextContexts")
        first = min(self, other, key=lambda tc: tc.doc_offset)
        if first is self:
            self.text = self.text[: other.doc_offset] + other.text
        else:
            self.doc_offset = other.doc_offset
            self.text = other.text[: first.doc_offset] + first.text
        return self

    @staticmethod
    def combine_many(text_contexts: list[_TextContext]) -> list[_TextContext]:
        text_contexts.sort(key=lambda t: (t.doc_id, t.doc_offset))
        combined = text_contexts[:1]
        for current in text_contexts[1:]:
            last = combined[-1]
            if last.overlaps(current):
                last.combine(current)
            else:
                combined.append(current)
        return combined


class IdentifiableSpan(CamelModel):
    id: int
    text: str
    start: int
    end: int
