import logging
from typing import Generator, Literal

from spacy.tokens import Doc

from narrativegraphs.nlp.common.annotation import SpanAnnotation
from narrativegraphs.nlp.common.entity_collector import SpanEntityCollector
from narrativegraphs.nlp.common.spacy import (
    calculate_batch_size,
    ensure_spacy_model,
)
from narrativegraphs.nlp.coref import FastCorefResolver
from narrativegraphs.nlp.coref.common import CoreferenceResolver
from narrativegraphs.nlp.entities.common import EntityExtractor

_logger = logging.getLogger("narrativegraphs.nlp.extraction")


class SpacyEntityExtractor(EntityExtractor, SpanEntityCollector):
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
        coref_resolver: Literal["fastcoref"] | CoreferenceResolver | None = None,
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
            coref_resolver: optional coreference resolver; when set, pronouns that
                resolve to a named antecedent are emitted with the resolved text
        """
        if model_name is None:
            model_name = "en_core_web_sm"
        self.nlp = ensure_spacy_model(model_name)
        if split_sentence_on_double_line_break:
            # Only add if not already present
            if "custom_sentencizer" not in self.nlp.pipe_names:
                self.nlp.add_pipe("custom_sentencizer", before="parser")

        if not named_entities and not noun_chunks:
            raise ValueError(
                "SpacyEntityExtractor requires at least named_entities or noun_chunks."
            )
        self.remove_pronouns = remove_pronouns

        if coref_resolver == "fastcoref":
            coref_resolver = FastCorefResolver()
        if coref_resolver is not None:
            coref_resolver.add_to_pipeline(self.nlp)

        SpanEntityCollector._init_collector(
            self, named_entities, noun_chunks, coref_resolver
        )

    def extract_entities_from_doc(self, doc: Doc) -> list[SpanAnnotation]:
        """Extract entities from a spaCy Doc.

        Args:
            doc: A spaCy Doc object

        Returns:
            extracted entities as SpanAnnotation objects
        """
        coref_map = self._build_coref_map(doc)

        result = []
        for span in self._collect_spans(doc, coref_map):
            is_pronoun = self._is_pronoun_only(span)
            if is_pronoun:
                if (span.start_char, span.end_char) in coref_map:
                    result.append(self._annotate(span, coref_map))
                elif not self.remove_pronouns:
                    result.append(SpanAnnotation.from_span(span))
                # else: unresolved pronoun + remove_pronouns=True → skip
            else:
                result.append(self._annotate(span, coref_map))
        return result

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
            batch_size = calculate_batch_size(texts, n_cpu)
        if n_cpu != 1:
            _logger.info("Using multiple CPU cores. Progress may stand still at first.")
        for doc in self.nlp.pipe(texts, n_process=n_cpu, batch_size=batch_size):
            yield self.extract_entities_from_doc(doc)
