"""Triplet (relation) extraction with an LLM."""

import logging
from typing import Any, Generator, Iterable, Optional

from narrativegraphs.nlp.common.annotation import AnnotationContext, SpanAnnotation
from narrativegraphs.nlp.common.llm import (
    DEFAULT_MODEL,
    LlmJsonClient,
    Span,
    align_sequence,
    align_span,
    map_completed,
    map_ordered,
)
from narrativegraphs.nlp.triplets.common import Triplet, TripletExtractor

_logger = logging.getLogger("narrativegraphs.nlp.extraction")

_SYSTEM_PROMPT = """\
You extract subject-predicate-object triplets from text for a narrative graph.

The user's extraction instructions:
{instructions}

Rules:
- Copy the subject, predicate and object verbatim from the text. Never \
paraphrase, translate, inflect or normalize them, and never introduce words \
that are not in the text. They are matched back against the source text \
character by character.
- Keep each part short: a subject or object is a noun phrase without its \
modifying clauses, a predicate is the verb and, where the relation needs it, \
its particle or preposition.
- The three parts must be non-overlapping spans of the same sentence, and must \
normally appear in the order subject, predicate, object.
- Quote that whole sentence, again verbatim, as the evidence.
- Resolve pronouns to the entity they refer to only if that entity is named \
elsewhere in the same sentence; otherwise skip the triplet.
- Extract only relations that are actually asserted by the text and that match \
the instructions above. Extracting nothing is a valid answer for a document \
that holds no such relations.
"""

_SCHEMA = {
    "type": "object",
    "properties": {
        "triplets": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "subject": {"type": "string"},
                    "predicate": {"type": "string"},
                    "object": {"type": "string"},
                    "evidence": {"type": "string"},
                },
                "required": ["subject", "predicate", "object", "evidence"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["triplets"],
    "additionalProperties": False,
}


class LlmTripletExtractor(TripletExtractor):
    """Extracts triplets by prompting an LLM with a plain-language instruction.

    In contrast to the rule-based extractors, what counts as a relation is
    stated rather than derived from the dependency parse:

        extractor = LlmTripletExtractor(
            "Extract relations between people, organizations and countries. "
            "Focus on who did what to whom politically."
        )
        pipeline = Pipeline(engine, triplet_extractor=extractor)

    Since the rest of the package addresses entities by their position in the
    document, every returned surface form is aligned back to the source text,
    and triplets whose parts cannot be found there are dropped.

    Requires optional dependency: anthropic>=1.0.0
    """

    def __init__(
        self,
        instructions: str,
        model: str = DEFAULT_MODEL,
        effort: str = "low",
        max_tokens: int = 16000,
        max_concurrent_requests: int = 4,
        client: Any = None,
    ):
        """
        Args:
            instructions: a short description of the entities and relations to
                extract, e.g. "extract relations between characters and the
                places they travel to"
            model: Claude model ID
            effort: thinking/token effort, one of "low", "medium", "high",
                "xhigh", "max"; raise it for instructions that call for
                genuine judgement
            max_tokens: cap on each response
            max_concurrent_requests: number of documents processed in parallel
                by `batch_extract`
            client: a pre-configured `anthropic.Anthropic` instance
        """
        if not instructions or not instructions.strip():
            raise ValueError(
                "instructions must describe which entities and relations to extract"
            )
        self.instructions = instructions.strip()
        self.max_concurrent_requests = max_concurrent_requests
        self._llm = LlmJsonClient(
            model=model, effort=effort, max_tokens=max_tokens, client=client
        )
        self._system_prompt = _SYSTEM_PROMPT.format(instructions=self.instructions)

    def extract(self, text: str) -> list[Triplet]:
        if not text or not text.strip():
            return []

        response = self._llm.request_json(self._system_prompt, text, _SCHEMA)
        if response is None:
            return []

        triplets = []
        for extracted in response.get("triplets", []):
            triplet = self._to_triplet(text, extracted)
            if triplet is not None:
                triplets.append(triplet)
        return triplets

    def batch_extract(
        self, texts: Iterable[str], n_cpu: int = 1, **kwargs
    ) -> Generator[list[Triplet], None, None]:
        """Extract from several documents, one request per document.

        Args:
            texts: an iterable of raw text strings
            n_cpu: ignored; requests are I/O-bound, so concurrency is governed
                by `max_concurrent_requests` instead
            **kwargs: unused

        Returns:
            yields triplets per text in the same order as the texts iterable
        """
        yield from map_ordered(
            self.extract, texts, max_workers=self.max_concurrent_requests
        )

    def batch_extract_unordered(
        self, texts: Iterable[str], n_cpu: int = 1, **kwargs
    ) -> Generator[tuple[int, list[Triplet]], None, None]:
        """Extract from several documents, handing over each as it comes back.

        Args:
            texts: an iterable of raw text strings
            n_cpu: ignored; requests are I/O-bound, so concurrency is governed
                by `max_concurrent_requests` instead
            **kwargs: unused

        Returns:
            yields (index, triplets) pairs in completion order, so that a slow
            document does not hold up the ones behind it
        """
        yield from map_completed(
            self.extract, texts, max_workers=self.max_concurrent_requests
        )

    def _to_triplet(self, text: str, extracted: dict[str, Any]) -> Optional[Triplet]:
        parts = [
            str(extracted.get(key, "")) for key in ("subject", "predicate", "object")
        ]
        if not all(part.strip() for part in parts):
            _logger.debug("Dropping triplet with an empty part: %s", extracted)
            return None

        evidence = align_span(text, str(extracted.get("evidence", "")))
        spans = align_sequence(text, parts, window=evidence)
        if spans is None:
            _logger.debug(
                "Dropping triplet whose parts are not in the text: %s", extracted
            )
            return None
        if _overlapping(spans):
            _logger.debug("Dropping triplet with overlapping parts: %s", extracted)
            return None

        subj, pred, obj = (
            SpanAnnotation(text=text[start:end], start_char=start, end_char=end)
            for start, end in spans
        )
        context = (
            AnnotationContext(
                text=text[evidence[0] : evidence[1]], doc_offset=evidence[0]
            )
            if evidence is not None
            else None
        )
        return Triplet(subj=subj, pred=pred, obj=obj, context=context)


def _overlapping(spans: list[Span]) -> bool:
    ordered = sorted(spans)
    return any(
        current[1] > following[0] for current, following in zip(ordered, ordered[1:])
    )
