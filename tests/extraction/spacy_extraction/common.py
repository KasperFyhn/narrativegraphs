from spacy.tokens import Span

from narrativegraphs.nlp.triplets.common import Triplet
from narrativegraphs.nlp.triplets.spacy.common import SpacyTripletExtractor


class DummySpacyTripletExtractor(SpacyTripletExtractor):
    def extract_triplets_from_sent(self, sent: Span) -> list[Triplet]:
        return []
