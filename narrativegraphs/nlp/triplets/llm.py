"""Triplet (relation) extraction with an LLM."""

import logging
from typing import Any, Generator, Iterable, Optional

from narrativegraphs.nlp.common.annotation import AnnotationContext, SpanAnnotation
from narrativegraphs.nlp.common.llm import (
    DEFAULT_BATCH_CHUNK_SIZE,
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


class _LlmTripletExtractor(TripletExtractor):
    """Shared prompt, schema and span alignment for the LLM triplet extractors.

    Subclasses differ only in how they get responses back: immediately, or
    through the Message Batches API.

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
            client: a pre-configured `anthropic.Anthropic` instance
        """
        if not instructions or not instructions.strip():
            raise ValueError(
                "instructions must describe which entities and relations to extract"
            )
        self.instructions = instructions.strip()
        self._llm = LlmJsonClient(
            model=model, effort=effort, max_tokens=max_tokens, client=client
        )
        self._system_prompt = _SYSTEM_PROMPT.format(instructions=self.instructions)

    def _triplets_from_response(
        self, text: str, response: Optional[dict[str, Any]]
    ) -> list[Triplet]:
        """Align one document's extracted triplets back onto its text."""
        if response is None:
            return []
        triplets = []
        for extracted in response.get("triplets", []):
            triplet = self._to_triplet(text, extracted)
            if triplet is not None:
                triplets.append(triplet)
        return triplets

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


class LlmTripletExtractor(_LlmTripletExtractor):
    """Extracts triplets by prompting an LLM with a plain-language instruction.

    In contrast to the rule-based extractors, what counts as a relation is
    stated rather than derived from the dependency parse:

        extractor = LlmTripletExtractor(
            "Extract relations between people, organizations and countries. "
            "Focus on who did what to whom politically."
        )
        pipeline = Pipeline(engine, triplet_extractor=extractor)

    One request per document, answered immediately. For a whole corpus,
    `LlmBatchTripletExtractor` does the same work at half the price.
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
                extract
            model: Claude model ID
            effort: thinking/token effort, one of "low", "medium", "high",
                "xhigh", "max"
            max_tokens: cap on each response
            max_concurrent_requests: number of documents in flight at a time
            client: a pre-configured `anthropic.Anthropic` instance
        """
        super().__init__(
            instructions,
            model=model,
            effort=effort,
            max_tokens=max_tokens,
            client=client,
        )
        self.max_concurrent_requests = max_concurrent_requests

    def extract(self, text: str) -> list[Triplet]:
        if not text or not text.strip():
            return []
        response = self._llm.request_json(self._system_prompt, text, _SCHEMA)
        return self._triplets_from_response(text, response)

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


class LlmBatchTripletExtractor(_LlmTripletExtractor):
    """Extracts triplets through the Message Batches API, at half the price.

    Requests are processed asynchronously: most batches finish within an hour,
    the limit is 24 hours, and a batch hands over nothing until it has ended in
    full. Documents are therefore submitted in chunks, and each chunk's results
    are stored as that chunk ends.

        extractor = LlmBatchTripletExtractor("Extract relations between ...")
        ng = NarrativeGraph(triplet_extractor=extractor).fit(docs)

    Results stay retrievable for 29 days, so the wait need not be sat through.
    `submit` sends the corpus off and returns the batch IDs; `collect` turns
    those IDs back into triplets whenever you next have the machine on:

        batch_ids = extractor.submit(docs)          # write these down
        # ... another day ...
        triplets = extractor.collect_all(batch_ids, docs)
        ng = NarrativeGraph().fit(docs, triplets=triplets)
    """

    def __init__(
        self,
        instructions: str,
        model: str = DEFAULT_MODEL,
        effort: str = "low",
        max_tokens: int = 16000,
        chunk_size: int = DEFAULT_BATCH_CHUNK_SIZE,
        poll_interval: float = 60.0,
        client: Any = None,
    ):
        """
        Args:
            instructions: a short description of the entities and relations to
                extract
            model: Claude model ID
            effort: thinking/token effort, one of "low", "medium", "high",
                "xhigh", "max"
            max_tokens: cap on each response
            chunk_size: documents per batch; smaller chunks mean results start
                landing sooner
            poll_interval: seconds between checks on a running batch
            client: a pre-configured `anthropic.Anthropic` instance
        """
        super().__init__(
            instructions,
            model=model,
            effort=effort,
            max_tokens=max_tokens,
            client=client,
        )
        self.chunk_size = chunk_size
        self.poll_interval = poll_interval

    def submit(self, texts: Iterable[str]) -> list[str]:
        """Send documents off for batch processing without waiting.

        Args:
            texts: the documents to extract from

        Returns:
            the ID of each submitted batch. Keep them: they are what `collect`
            needs to pick the results up later, and results remain available
            for 29 days.
        """
        prompts = [(_custom_id(index), text) for index, text in _extractable(texts)]
        if not prompts:
            return []
        return self._llm.submit_batches(
            self._system_prompt, prompts, _SCHEMA, chunk_size=self.chunk_size
        )

    def collect(
        self, batch_ids: Iterable[str], texts: Iterable[str]
    ) -> Generator[tuple[int, list[Triplet]], None, None]:
        """Wait for submitted batches and yield triplets as each chunk ends.

        Args:
            batch_ids: the IDs returned by `submit`
            texts: the same documents, in the same order, that were submitted;
                needed because aligning a triplet requires its source text

        Returns:
            yields (index, triplets) pairs, in the order results come back
        """
        texts = list(texts)
        # Documents that were never submitted still belong in the output, so
        # that a caller sees every document accounted for.
        submitted = dict(_extractable(texts))
        for index in range(len(texts)):
            if index not in submitted:
                yield index, []

        for custom_id, response in self._llm.collect_batches(
            batch_ids, poll_interval=self.poll_interval
        ):
            index = _index_from_custom_id(custom_id, len(texts))
            if index is None:
                _logger.warning("Ignoring result with unexpected id %r", custom_id)
                continue
            yield index, self._triplets_from_response(texts[index], response)

    def collect_all(
        self, batch_ids: Iterable[str], texts: Iterable[str]
    ) -> list[list[Triplet]]:
        """Collect submitted batches into one list of triplets per document.

        The shape `Pipeline.run` and `NarrativeGraph.fit` accept as
        pre-computed annotations.
        """
        texts = list(texts)
        collected: list[list[Triplet]] = [[] for _ in texts]
        for index, triplets in self.collect(batch_ids, texts):
            collected[index] = triplets
        return collected

    def extract(self, text: str) -> list[Triplet]:
        """Extract from a single document by submitting a batch of one.

        Batching a lone document buys nothing but the lower price, and still
        waits for the batch to end. Prefer `batch_extract_unordered`.
        """
        for _, triplets in self.batch_extract_unordered([text]):
            return triplets
        return []

    def batch_extract(
        self, texts: Iterable[str], n_cpu: int = 1, **kwargs
    ) -> Generator[list[Triplet], None, None]:
        """Extract from several documents, yielding them in input order.

        Batch results arrive out of order, so this holds them until the run is
        done. `batch_extract_unordered` hands each chunk over as it lands.
        """
        texts = list(texts)
        collected = self.collect_all(self.submit(texts), texts)
        yield from collected

    def batch_extract_unordered(
        self, texts: Iterable[str], n_cpu: int = 1, **kwargs
    ) -> Generator[tuple[int, list[Triplet]], None, None]:
        """Submit all documents, then yield each chunk's results as it ends.

        Args:
            texts: an iterable of raw text strings
            n_cpu: ignored; the work happens on Anthropic's infrastructure
            **kwargs: unused

        Returns:
            yields (index, triplets) pairs, in the order results come back
        """
        texts = list(texts)
        yield from self.collect(self.submit(texts), texts)


def _custom_id(index: int) -> str:
    """Identify a request by its document's position in the input."""
    return f"doc-{index}"


def _index_from_custom_id(custom_id: str, count: int) -> Optional[int]:
    prefix, _, raw_index = custom_id.rpartition("-")
    if prefix != "doc" or not raw_index.isdigit():
        return None
    index = int(raw_index)
    return index if index < count else None


def _extractable(texts: Iterable[str]) -> list[tuple[int, str]]:
    """The documents worth sending: an empty one has nothing to extract."""
    return [(index, text) for index, text in enumerate(texts) if text and text.strip()]


def _overlapping(spans: list[Span]) -> bool:
    ordered = sorted(spans)
    return any(
        current[1] > following[0] for current, following in zip(ordered, ordered[1:])
    )
