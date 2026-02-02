from abc import ABC

from narrativegraphs.db.documents import DocumentOrm
from narrativegraphs.nlp.triplets.common import SpanAnnotation, Tuplet


class CooccurrenceExtractor(ABC):
    def extract(self, doc: DocumentOrm, entities: list[SpanAnnotation]) -> list[Tuplet]:
        pass
