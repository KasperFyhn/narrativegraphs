from narrativegraph.nlp.extraction import TripletExtractor
from narrativegraph.nlp.extraction.common import Triplet, TripletPart
from narrativegraph.nlp.mapping import Mapper


class MockTripletExtractor(TripletExtractor):

    def extract(self, text: str) -> list[Triplet]:
        tokens = text.split()
        if len(tokens) < 2:
            return []

        subject = tokens[0]
        subject_start = text.find(subject)
        subject_end = text.find(subject) + len(subject)
        predicate = tokens[1]
        predicate_start = text.find(predicate)
        predicate_end = text.find(predicate) + len(predicate)
        object_ = tokens[2]
        object_start = text.find(object_)
        object_end = text.find(object_) + len(object_)

        return [
            Triplet(
                subj=TripletPart(
                    text=subject, start_char=subject_start, end_char=subject_end
                ),
                pred=TripletPart(
                    text=predicate, start_char=predicate_start, end_char=predicate_end
                ),
                obj=TripletPart(
                    text=object_, start_char=object_start, end_char=object_end
                ),
            )
        ]


class MockMapper(Mapper):
    def create_mapping(self, labels: list[str]) -> dict[str, str]:
        return {label: label for label in labels}
