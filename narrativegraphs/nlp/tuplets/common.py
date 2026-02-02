from abc import ABC

from narrativegraphs.db.documents import DocumentOrm
from narrativegraphs.nlp.common.annotation import SpanAnnotation
from narrativegraphs.nlp.triplets.common import Tuplet


class CooccurrenceExtractor(ABC):
    def extract(self, doc: DocumentOrm, entities: list[SpanAnnotation]) -> list[Tuplet]:
        pass
