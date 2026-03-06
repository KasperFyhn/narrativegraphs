from spacy.tokens import Doc, Span

from narrativegraphs.nlp.common.annotation import SpanAnnotation
from narrativegraphs.nlp.common.spacy import (
    filter_by_range,
    fits_in_range,
    spans_overlap,
)
from narrativegraphs.nlp.coref import CoreferenceResolver

CorefMap = dict[tuple[int, int], str]


class SpanEntityCollector:
    """Mixin for NER + noun-chunk collection, coref resolution, and SpanAnnotation
    building.

    Concrete classes must set self.nlp and register
    `coref_resolver.add_to_pipeline(self.nlp)` themselves before calling
    `_init_collector` — this mixin does not own self.nlp.

    The coref map is built per-doc via _build_coref_map and threaded explicitly to
    _collect_spans, _annotate, and _is_unresolved_pronoun rather than stored as instance
    state, so there is no implicit ordering requirement between calls.
    """

    def _init_collector(
        self,
        named_entities: bool | tuple[int, int | None],
        noun_chunks: bool | tuple[int, int | None],
        coref_resolver: CoreferenceResolver | None = None,
    ) -> None:
        self.ner = named_entities
        self.noun_chunks = noun_chunks
        self.coref_resolver = coref_resolver

    def _is_allowed_entity(self, span: Span) -> bool:
        """Check if span is allowed based on NER/noun_chunks settings."""
        if all(t.ent_type_ for t in span):  # NER land
            if isinstance(self.ner, tuple):
                return fits_in_range(span, self.ner)
            else:
                return bool(self.ner)
        else:  # NP land
            if isinstance(self.noun_chunks, tuple):
                return fits_in_range(span, self.noun_chunks)
            else:
                return bool(self.noun_chunks)

    @staticmethod
    def _is_pronoun_only(span: Span) -> bool:
        """Check if span consists only of pronouns."""
        return all(t.pos_ == "PRON" for t in span)

    def _is_unresolved_pronoun(self, span: Span, coref_map: CorefMap) -> bool:
        """Check if span is a pronoun with no coref resolution."""
        return (
            self._is_pronoun_only(span)
            and (span.start_char, span.end_char) not in coref_map
        )

    def _build_coref_map(self, doc: Doc) -> CorefMap:
        """Build and return a coref map for the given doc.

        Only pronominal mentions are resolved, and only to antecedents that would
        themselves be extracted by the normal NER/noun-chunk pipeline (i.e. present
        in _collect_spans with an empty coref map). This ensures resolution targets
        are coherent entities and excludes long descriptive NPs, relative clauses,
        and other spans that would not survive ordinary extraction.

        Returns an empty dict if no resolver is set.
        """
        if not self.coref_resolver:
            return {}

        # Valid targets = spans the extractor would produce without any coref.
        valid_spans = {
            (span.start_char, span.end_char)
            for span in self._collect_spans(doc, {})
        }

        result: CorefMap = {}
        for (pron_start, pron_end), (
            ant_text,
            head_start,
            head_end,
        ) in self.coref_resolver.resolve_doc(doc).items():
            mention_span = doc.char_span(pron_start, pron_end)
            if mention_span is None or not self._is_pronoun_only(mention_span):
                continue
            if (head_start, head_end) in valid_spans:
                result[(pron_start, pron_end)] = ant_text
        return result

    def _collect_spans(self, source: Span | Doc, coref_map: CorefMap) -> list[Span]:
        """Collect non-overlapping entity spans with NER priority over noun chunks.

        NER entities (priority 0) are preferred over noun chunks (priority 1).
        Pronouns present in coref_map bypass size filters so they survive to the
        result-building step. Returns spans sorted by start_char.
        """
        candidates = []

        if self.ner:
            ents = list(source.ents)
            if isinstance(self.ner, tuple):
                ents = filter_by_range(ents, self.ner)
            ents = [
                e for e in ents if list(e)[0].ent_type_ not in {"CARDINAL", "ORDINAL"}
            ]
            candidates.extend((span, 0) for span in ents)  # NER priority: 0

        if self.noun_chunks:
            chunks = list(source.noun_chunks)
            chunks = [
                c
                for c in chunks
                if self._is_allowed_entity(c)
                or (
                    self._is_pronoun_only(c) and (c.start_char, c.end_char) in coref_map
                )
            ]
            candidates.extend((span, 1) for span in chunks)  # Noun chunk priority: 1

        # Sort by priority: NER first, then length desc, then position
        candidates.sort(key=lambda x: (x[1], -len(x[0]), x[0].start))

        # Greedily select non-overlapping spans
        entities: list[Span] = []
        for target, _ in candidates:
            if not any(spans_overlap(target, other) for other in entities):
                entities.append(target)

        entities.sort(key=lambda x: x.start_char)
        return entities

    def _annotate(self, span: Span, coref_map: CorefMap) -> SpanAnnotation:
        """Build SpanAnnotation, using resolved text from coref_map if available."""
        resolved = coref_map.get((span.start_char, span.end_char))
        if resolved:
            return SpanAnnotation(
                text=resolved,
                start_char=span.start_char,
                end_char=span.end_char,
                normalized_text=resolved.lower(),
                is_coref_resolved=True,
            )
        return SpanAnnotation.from_span(span)
