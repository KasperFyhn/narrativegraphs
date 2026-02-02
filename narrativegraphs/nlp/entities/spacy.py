import logging
from typing import Generator, Iterable

from spacy.tokens import Doc, Span

from narrativegraphs.nlp.entities.common import EntityExtractor
from narrativegraphs.nlp.triplets.common import SpanAnnotation
from narrativegraphs.nlp.triplets.spacy.common import (
    _calculate_batch_size,
    _ensure_spacy_model,
)

_logger = logging.getLogger("narrativegraphs.nlp.extraction")


class SpacyEntityExtractor(EntityExtractor):
    """Entity extractor using spaCy NER and/or noun chunks.

    Extracts entities from text using named entity recognition and/or noun chunks,
    with NER having priority over noun chunks when spans overlap. Uses greedy
    non-overlapping selection to avoid duplicate entities.
    """

    def __init__(
        self,
        model_name: str = None,
        named_entities: bool | tuple[int, int | None] = (1, None),
        noun_chunks: bool | tuple[int, int | None] = (2, None),
        remove_pronouns: bool = True,
        split_sentence_on_double_line_break: bool = True,
    ):
        """
        Args:
            model_name: name of the spaCy model to use (default: en_core_web_sm)
            named_entities: False to disable NER, True to enable all,
                or tuple (min_tokens, max_tokens) to filter by length
            noun_chunks: False to disable noun chunks, True to enable all,
                or tuple (min_tokens, max_tokens) to filter by length
            remove_pronouns: whether to filter out pronoun-only spans
            split_sentence_on_double_line_break: adds extra sentence boundaries on
                double line breaks ("\\n\\n")
        """
        if model_name is None:
            model_name = "en_core_web_sm"
        self.nlp = _ensure_spacy_model(model_name)
        if split_sentence_on_double_line_break:
            # Only add if not already present
            if "custom_sentencizer" not in self.nlp.pipe_names:
                from narrativegraphs.nlp.utils.spacysegmentation import (  # noqa
                    custom_sentencizer,
                )

                self.nlp.add_pipe("custom_sentencizer", before="parser")

        if not named_entities and not noun_chunks:
            raise ValueError(
                "SpacyEntityExtractor requires at least named_entities or noun_chunks."
            )
        self.ner = named_entities
        self.noun_chunks = noun_chunks
        self.remove_pronouns = remove_pronouns

    @staticmethod
    def _fits_in_range_tuple(span: Span, range_: tuple[int, int | None]) -> bool:
        """Check if span length fits within the specified range."""
        lower_bound, upper_bound = range_
        return len(span) >= lower_bound and (
            upper_bound is None or len(span) < upper_bound
        )

    def _is_allowed_entity(self, span: Span) -> bool:
        """Check if span is allowed based on NER/noun_chunks settings."""
        if all(t.ent_type_ for t in span):  # NER land
            if isinstance(self.ner, tuple):
                return self._fits_in_range_tuple(span, self.ner)
            else:
                return bool(self.ner)
        else:  # NP land
            if isinstance(self.noun_chunks, tuple):
                return self._fits_in_range_tuple(span, self.noun_chunks)
            else:
                return bool(self.noun_chunks)

    @staticmethod
    def _filter_by_range(
        spans: Iterable[Span], range_: tuple[int, int | None]
    ) -> list[Span]:
        """Filter spans by token length range."""
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

    def _is_pronoun_only(self, span: Span) -> bool:
        """Check if span consists only of pronouns."""
        return all(t.pos_ == "PRON" for t in span)

    def extract_entities_from_doc(self, doc: Doc) -> list[SpanAnnotation]:
        """Extract entities from a spaCy Doc.

        Args:
            doc: A spaCy Doc object

        Returns:
            extracted entities as SpanAnnotation objects
        """
        # Collect entities with priority scoring
        candidates = []

        if self.ner:
            ents = doc.ents
            if isinstance(self.ner, tuple):
                ents = self._filter_by_range(ents, self.ner)
            # Filter out numeric entity types
            ents = [
                e for e in ents if list(e)[0].ent_type_ not in {"CARDINAL", "ORDINAL"}
            ]
            candidates.extend((span, 0) for span in ents)  # NER priority: 0

        if self.noun_chunks:
            chunks = list(doc.noun_chunks)
            if isinstance(self.noun_chunks, tuple):
                chunks = self._filter_by_range(chunks, self.noun_chunks)
            # Filter chunks that pass _is_allowed_entity check
            chunks = [c for c in chunks if self._is_allowed_entity(c)]
            candidates.extend((span, 1) for span in chunks)  # Noun chunk priority: 1

        # Sort by priority: NER first, then length desc, then position
        candidates.sort(key=lambda x: (x[1], -len(x[0]), x[0].start))

        # Greedily select non-overlapping spans
        entities = []
        for target, _ in candidates:
            if not any(self._spans_overlap(target, other) for other in entities):
                entities.append(target)

        # Sort by position
        entities.sort(key=lambda x: x.start_char)

        # Filter pronouns if requested
        if self.remove_pronouns:
            entities = [e for e in entities if not self._is_pronoun_only(e)]

        return [SpanAnnotation.from_span(e) for e in entities]

    def extract(self, text: str) -> list[SpanAnnotation]:
        """Extract entities from a text string.

        Args:
            text: raw text string

        Returns:
            extracted entities as SpanAnnotation objects
        """
        doc = self.nlp(text)
        return self.extract_entities_from_doc(doc)

    def batch_extract(
        self, texts: list[str], n_cpu: int = 1, batch_size: int = None
    ) -> Generator[list[SpanAnnotation], None, None]:
        """Extract entities from multiple texts.

        Args:
            texts: list of raw text strings
            n_cpu: number of CPUs to use for parallel processing
            batch_size: batch size for spaCy pipe (auto-calculated if None)

        Returns:
            generator yielding entities per text in input order
        """
        if batch_size is None:
            batch_size = _calculate_batch_size(texts, n_cpu)
        _logger.info("Using multiple CPU cores. Progress may stand still at first.")
        for doc in self.nlp.pipe(texts, n_process=n_cpu, batch_size=batch_size):
            yield self.extract_entities_from_doc(doc)
