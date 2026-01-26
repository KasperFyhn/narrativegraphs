from typing import Iterable

from spacy.tokens import Span

from narrativegraphs.nlp.extraction.common import SpanAnnotation, Triplet
from narrativegraphs.nlp.extraction.spacy.common import SpacyTripletExtractor


class NaiveSpacyTripletExtractor(SpacyTripletExtractor):
    def __init__(
        self,
        model_name: str = None,
        named_entities: bool | tuple[int, int | None] = (1, None),
        noun_chunks: bool | tuple[int, int | None] = (2, None),
        max_tokens_between: int = 4,
        split_sentence_on_double_line_break: bool = True,
    ):
        super().__init__(
            model_name,
            split_sentence_on_double_line_break=split_sentence_on_double_line_break,
        )
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

    @staticmethod
    def _spans_overlap(span1: Span, span2: Span) -> bool:
        """Check if spans overlap at character level."""
        return not (
            span1.end_char <= span2.start_char or span2.end_char <= span1.start_char
        )

    def extract_triplets_from_sent(self, sent: Span) -> list[Triplet]:
        triplets = []

        # Collect entities with priority scoring
        candidates = []
        if self.ner:
            ents = sent.ents
            if isinstance(self.ner, tuple):
                ents = self._filter_by_range(ents, self.ner)
            ents = [
                e for e in ents if list(e)[0].ent_type_ not in {"CARDINAL", "ORDINAL"}
            ]
            candidates.extend((span, 0) for span in ents)  # NER priority: 0

        if self.noun_chunks:
            chunks = sent.noun_chunks
            if isinstance(self.noun_chunks, tuple):
                chunks = self._filter_by_range(chunks, self.noun_chunks)
            candidates.extend((span, 1) for span in chunks)  # Noun chunk priority: 1

        # Sort by priority: NER first, then length desc, then position
        candidates.sort(key=lambda x: (x[1], -len(x[0]), x[0].start))

        # Greedily select non-overlapping spans
        entities = []
        for target, _ in candidates:
            if not any(self._spans_overlap(target, other) for other in entities):
                entities.append(target)

        entities.sort(key=lambda x: x.start_char)

        # Create triplets from adjacent entities
        for i in range(len(entities) - 1):
            subj, obj = entities[i], entities[i + 1]
            if obj.start - subj.end > self.max_tokens_between:
                continue

            pred = sent.doc[subj.end : obj.start]

            # skip if no predicate
            if len(pred) == 0:
                continue

            triplets.append(
                Triplet(
                    subj=SpanAnnotation.from_span(subj),
                    pred=SpanAnnotation.from_span(pred),
                    obj=SpanAnnotation.from_span(obj),
                )
            )

        return triplets
