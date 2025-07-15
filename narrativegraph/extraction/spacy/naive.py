from typing import Tuple, Iterable

from spacy.tokens import Span

from narrativegraph.extraction.common import Triplet, TripletPart
from narrativegraph.extraction.spacy.common import SpacyTripletExtractor


class NaiveSpacyTripletExtractor(SpacyTripletExtractor):

    def __init__(
        self,
        model_name: str = None,
        named_entities: bool | tuple[int, int | None] = (1, None),
        noun_chunks: bool | tuple[int, int | None] = (2, None),
        max_tokens_between: int = 4,
    ):
        super().__init__(model_name)
        if not named_entities and not noun_chunks:
            raise NotImplementedError(
                "Naive spacy requires at least named_entities or noun_chunks."
            )
        self.ner = named_entities
        self.noun_chunks = noun_chunks
        self.max_tokens_between = max_tokens_between

    @staticmethod
    def _filter_by_range(spans: Iterable[Span], range_: tuple[int, int]) -> list[Span]:
        result = []
        lower_bound, upper_bound = range_
        for span in spans:
            if len(span) >= lower_bound and (
                upper_bound is None or len(span) < upper_bound
            ):
                result.append(span)
        return result


    def extract_triplets_from_sent(self, sent: Span) -> list[Triplet]:
        triplets = []

        # get ner and/or noun chunks in an ordered list
        entities: list[Span] = []
        if self.ner:
            ents = sent.ents
            if isinstance(self.ner, tuple):
                ents = self._filter_by_range(ents, self.ner)
            entities.extend(ents)
        if self.noun_chunks:
            chunks = sent.noun_chunks
            if isinstance(self.ner, tuple):
                chunks = self._filter_by_range(chunks, self.noun_chunks)
            entities.extend(chunks)

        entities.sort(key=lambda x: x.start_char)

        # for each (i, i+1) pair, create a triplet with the text between them
        for i in range(len(entities) - 1):
            subj = entities[i]
            obj = entities[i + 1]

            # skip if the distance is too big
            if obj.start - subj.end > self.max_tokens_between:
                continue

            pred = sent[subj.end : obj.start]

            # skip if no predicate
            if len(pred) == 0:
                continue

            subj_span = TripletPart.from_span(subj)
            pred_span = TripletPart.from_span(pred)
            obj_span = TripletPart.from_span(obj)

            triplets.append(Triplet(subj=subj_span, pred=pred_span, obj=obj_span))

        return triplets
