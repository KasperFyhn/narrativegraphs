from narrativegraphs.nlp.entities.common import EntityExtractor
from narrativegraphs.nlp.mapping import Mapper
from narrativegraphs.nlp.triplets import TripletExtractor
from narrativegraphs.nlp.triplets.common import SpanAnnotation, Triplet


class MockEntityExtractor(EntityExtractor):
    """Mock entity extractor that treats capitalized words as entities."""

    def extract(self, text: str) -> list[SpanAnnotation]:
        entities = []
        pos = 0
        for word in text.split():
            start = text.find(word, pos)
            end = start + len(word)
            clean_word = word.strip(".,!?;:")
            if clean_word and clean_word[0].isupper():
                entities.append(
                    SpanAnnotation(
                        text=clean_word,
                        start_char=start,
                        end_char=start + len(clean_word),
                    )
                )
            pos = end
        return entities


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
                subj=SpanAnnotation(
                    text=subject, start_char=subject_start, end_char=subject_end
                ),
                pred=SpanAnnotation(
                    text=predicate, start_char=predicate_start, end_char=predicate_end
                ),
                obj=SpanAnnotation(
                    text=object_, start_char=object_start, end_char=object_end
                ),
            )
        ]


class MockMapper(Mapper):
    def create_mapping(self, labels: list[str]) -> dict[str, str]:
        return {label: label for label in labels}
