from abc import ABC
from typing import Optional

from pydantic import BaseModel

from narrativegraphs.db.documents import DocumentOrm
from narrativegraphs.nlp.common.annotation import AnnotationContext, SpanAnnotation


class Tuplet(BaseModel):
    entity_one: SpanAnnotation
    entity_two: SpanAnnotation
    context: Optional[AnnotationContext] = None


class CooccurrenceExtractor(ABC):
    def extract(self, doc: DocumentOrm, entities: list[SpanAnnotation]) -> list[Tuplet]:
        pass
