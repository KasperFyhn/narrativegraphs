from abc import ABC

from pydantic import BaseModel

from narrativegraphs.db.documents import DocumentOrm
from narrativegraphs.nlp.common.annotation import SpanAnnotation


class Tuplet(BaseModel):
    entity_one: SpanAnnotation
    entity_two: SpanAnnotation


class CooccurrenceExtractor(ABC):
    def extract(self, doc: DocumentOrm, entities: list[SpanAnnotation]) -> list[Tuplet]:
        pass
