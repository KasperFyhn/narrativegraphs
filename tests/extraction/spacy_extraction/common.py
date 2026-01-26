from spacy.tokens import Span

from narrativegraphs.nlp.extraction.common import Triplet
from narrativegraphs.nlp.extraction.spacy.common import SpacyTripletExtractor


class DummySpacyTripletExtractor(SpacyTripletExtractor):
    def extract_triplets_from_sent(self, sent: Span) -> list[Triplet]:
        return []
