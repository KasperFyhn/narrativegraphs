from spacy.tokens import Doc, Span

from narrativegraphs.nlp.common.annotation import AnnotationContext, SpanAnnotation
from narrativegraphs.nlp.common.spacy import CorefMap, SpanEntityCollector
from narrativegraphs.nlp.coref.common import CoreferenceResolver
from narrativegraphs.nlp.triplets.common import Triplet
from narrativegraphs.nlp.triplets.spacy.common import SpacyTripletExtractor


class NaiveSpacyTripletExtractor(SpacyTripletExtractor):
    def __init__(
        self,
        model_name: str = None,
        named_entities: bool | tuple[int, int | None] = (1, None),
        noun_chunks: bool | tuple[int, int | None] = (2, None),
        max_tokens_between: int = 4,
        coref_resolver: CoreferenceResolver | None = None,
        remove_pronoun_entities: bool = True,
        split_sentence_on_double_line_break: bool = True,
    ):
        super().__init__(
            model_name,
            split_sentence_on_double_line_break=split_sentence_on_double_line_break,
            coref_resolver=coref_resolver,
        )
        if not named_entities and not noun_chunks:
            raise NotImplementedError(
                "Naive spacy requires at least named_entities or noun_chunks."
            )
        self.max_tokens_between = max_tokens_between
        self.remove_pronoun_entities = remove_pronoun_entities
        self._collector = SpanEntityCollector(named_entities, noun_chunks)

    def extract_triplets_from_doc(self, doc: Doc) -> list[Triplet]:
        coref_map = self._collector.build_coref_map(doc)
        triplets = []
        for sent in doc.sents:
            sent_triplets = self.extract_triplets_from_sent(sent, coref_map)
            if sent_triplets:
                triplets.extend(sent_triplets)
        return triplets

    def extract_triplets_from_sent(
        self, sent: Span, coref_map: CorefMap | None = None
    ) -> list[Triplet]:
        if coref_map is None:
            coref_map = {}
        triplets = []

        entities = [
            s
            for s in self._collector.collect_spans(sent, coref_map)
            if not (
                self.remove_pronoun_entities
                and self._collector.is_unresolved_pronoun(s, coref_map)
            )
        ]

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
                    subj=self._collector.annotate(subj, coref_map),
                    pred=SpanAnnotation.from_span(pred),
                    obj=self._collector.annotate(obj, coref_map),
                    context=AnnotationContext.from_span(sent),
                )
            )

        return triplets
