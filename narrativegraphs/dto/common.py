from datetime import date
from typing import Optional

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

    @classmethod
    def from_mixin(cls, orm: AnnotationBackedTextStatsMixin):
        return cls(
            frequency=orm.frequency,
            doc_frequency=orm.doc_frequency,
            adjusted_tf_idf=orm.adjusted_tf_idf,
            first_occurrence=orm.first_occurrence,
            last_occurrence=orm.last_occurrence,
        )


class TextOccurrence(BaseDetails):
    stats: TextOccurrenceStats


class LabeledTextOccurrence(TextOccurrence):
    label: str
    alt_labels: Optional[list[str]] = None
