"""Common spaCy utilities shared across entity and triplet extraction."""

import logging

import psutil
import spacy
from spacy import Language
from spacy.tokens import Doc, Span

from narrativegraphs.nlp.common.annotation import SpanAnnotation
from narrativegraphs.nlp.coref import CoreferenceResolver

if not Doc.has_extension("coref_resolutions"):
    Doc.set_extension("coref_resolutions", default=None)

_logger = logging.getLogger("narrativegraphs.nlp")


def calculate_batch_size(texts: list[str], n_cpu: int = -1) -> int:
    """Simple heuristic-based batch size calculation."""
    if not texts:
        raise ValueError("No texts provided.")

    avg_length = sum(len(text) for text in texts) / len(texts)

    actual_cpu_count = (
        psutil.cpu_count() if n_cpu == -1 else min(n_cpu, psutil.cpu_count())
    )

    if avg_length < 100:
        base_size = 1000
    elif avg_length < 500:
        base_size = 500
    elif avg_length < 2000:
        base_size = 200
    elif avg_length < 5000:
        base_size = 100
    else:
        base_size = 50

    scaled_size = base_size * max(1, actual_cpu_count // 4)
    return max(10, min(scaled_size, 2000))


def ensure_spacy_model(name: str):
    """Ensure spaCy model is available, downloading if necessary."""
    try:
        return spacy.load(name)
    except OSError:
        _logger.info(
            f"First-time setup: downloading spaCy model '{name}'. "
            f"This is a one-time download (~50-500MB depending on model) "
            f"and may take a few minutes..."
        )

        try:
            spacy.cli.download(name)
            return spacy.load(name)
        except Exception as e:
            _logger.error(f"Failed to download model '{name}': {e}")
            raise RuntimeError(
                f"Could not automatically download spaCy model '{name}'.\n"
                f"Please install it manually with:\n"
                f"  python -m spacy download {name}\n"
                f"If you continue to have issues, see: "
                f"https://spacy.io/usage/models"
            ) from e


@Language.component("custom_sentencizer")
def custom_sentencizer(doc):
    for i, token in enumerate(doc[:-1]):
        if token.text == "\n\n":
            doc[i + 1].is_sent_start = True

    return doc


def build_spacy_pipeline(
    model_name: str,
    split_sentence_on_double_line_break: bool,
    coref_resolver: bool | CoreferenceResolver | None = None,
) -> Language:
    """Load a spaCy model and wire up sentencizer and coref annotation."""

    nlp = ensure_spacy_model(model_name)

    if split_sentence_on_double_line_break:
        if "custom_sentencizer" not in nlp.pipe_names:
            nlp.add_pipe("custom_sentencizer", before="parser")

    if coref_resolver is True:
        from narrativegraphs.nlp.coref import FastCorefResolver

        coref_resolver = FastCorefResolver()

    if coref_resolver is not None:
        coref_resolver.add_to_pipeline(nlp)

        # The resolve_doc method of a CoreferenceResolver may rely on instance
        # variables (for one reason or the other). Therefore, we need to have a unique
        # for each instance registed in SpaCy.
        component_name = (
            f"{type(coref_resolver).__name__}-{id(coref_resolver)}_resolve_doc"
        )

        def _make_annotator(resolver):
            def _annotate(doc):
                doc._.coref_resolutions = resolver.resolve_doc(doc)
                return doc

            return _annotate

        Language.component(component_name, func=_make_annotator(coref_resolver))
        nlp.add_pipe(component_name)

    return nlp


CorefMap = dict[tuple[int, int], str]


class SpanEntityCollector:
    """NER + noun-chunk collection, coref resolution, and SpanAnnotation building."""

    def __init__(
        self,
        named_entities: bool | tuple[int, int | None],
        noun_chunks: bool | tuple[int, int | None],
    ) -> None:
        self.ner = named_entities
        self.noun_chunks = noun_chunks

    @staticmethod
    def fits_in_range(span: Span, range_: tuple[int, int | None]) -> bool:
        """Check if span length fits within the specified range."""
        lower_bound, upper_bound = range_
        return len(span) >= lower_bound and (
            upper_bound is None or len(span) < upper_bound
        )

    @staticmethod
    def spans_overlap(span1: Span, span2: Span) -> bool:
        """Check if two spans overlap at character level."""
        return not (
            span1.end_char <= span2.start_char or span2.end_char <= span1.start_char
        )

    def is_allowed_entity(self, span: Span) -> bool:
        """Check if span is allowed based on NER/noun_chunks settings."""
        if all(t.ent_type_ for t in span):  # NER land
            if isinstance(self.ner, tuple):
                return self.fits_in_range(span, self.ner)
            else:
                return bool(self.ner)
        else:  # NP land
            if isinstance(self.noun_chunks, tuple):
                return self.fits_in_range(span, self.noun_chunks)
            else:
                return bool(self.noun_chunks)

    @staticmethod
    def is_pronoun_only(span: Span) -> bool:
        """Check if span consists only of pronouns."""
        return all(t.pos_ == "PRON" for t in span)

    def is_unresolved_pronoun(self, span: Span, coref_map: CorefMap) -> bool:
        """Check if span is a pronoun with no coref resolution."""
        return (
            self.is_pronoun_only(span)
            and (span.start_char, span.end_char) not in coref_map
        )

    def build_coref_map(self, doc: Doc) -> CorefMap:
        """Build and return a coref map for the given doc.

        Only pronominal mentions are resolved, and only to antecedents that would
        themselves be extracted by the normal NER/noun-chunk pipeline (i.e. present
        in _collect_spans with an empty coref map). This ensures resolution targets
        are coherent entities and excludes long descriptive NPs, relative clauses,
        and other spans that would not survive ordinary extraction.

        Returns an empty dict if no coref annotations are present on the doc.
        """
        raw_resolutions = doc._.coref_resolutions or {}
        if not raw_resolutions:
            return {}

        # Valid targets = spans the extractor would produce without any coref.
        valid_spans = {
            (span.start_char, span.end_char) for span in self.collect_spans(doc, {})
        }

        result: CorefMap = {}
        for (pron_start, pron_end), (
            ant_text,
            head_start,
            head_end,
        ) in raw_resolutions.items():
            mention_span = doc.char_span(pron_start, pron_end)
            if mention_span is None or not self.is_pronoun_only(mention_span):
                continue
            if (head_start, head_end) in valid_spans:
                result[(pron_start, pron_end)] = ant_text
        return result

    def collect_spans(self, source: Span | Doc, coref_map: CorefMap) -> list[Span]:
        """Collect non-overlapping entity spans with NER priority over noun chunks.

        NER entities (priority 0) are preferred over noun chunks (priority 1).
        Pronouns present in coref_map bypass size filters so they survive to the
        result-building step. Returns spans sorted by start_char.
        """
        candidates = []

        if self.ner:
            ents = list(source.ents)
            if isinstance(self.ner, tuple):
                ents = [e for e in ents if self.fits_in_range(e, self.ner)]
            ents = [
                e for e in ents if list(e)[0].ent_type_ not in {"CARDINAL", "ORDINAL"}
            ]
            candidates.extend((span, 0) for span in ents)  # NER priority: 0

        if self.noun_chunks:
            chunks = list(source.noun_chunks)
            chunks = [
                c
                for c in chunks
                if self.is_allowed_entity(c)
                or (self.is_pronoun_only(c) and (c.start_char, c.end_char) in coref_map)
            ]
            candidates.extend((span, 1) for span in chunks)  # Noun chunk priority: 1

        # Sort by priority: NER first, then length desc, then position
        candidates.sort(key=lambda x: (x[1], -len(x[0]), x[0].start))

        # Greedily select non-overlapping spans
        entities: list[Span] = []
        for target, _ in candidates:
            if not any(self.spans_overlap(target, other) for other in entities):
                entities.append(target)

        entities.sort(key=lambda x: x.start_char)
        return entities

    @staticmethod
    def annotate(span: Span, coref_map: CorefMap) -> SpanAnnotation:
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
