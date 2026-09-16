"""Triplet (relation) extraction with an LLM."""

import logging
import threading
from dataclasses import dataclass
from typing import Any, Generator, Iterable, Optional

from pydantic import BaseModel, ConfigDict, ValidationError

from narrativegraphs.nlp.common.annotation import AnnotationContext, SpanAnnotation
from narrativegraphs.nlp.common.llm import (
    DEFAULT_BATCH_CHUNK_SIZE,
    AnthropicClient,
    BatchLlmClient,
    LlmClient,
    Span,
    align_sequence,
    align_span,
    json_schema_of,
    map_ordered,
)
from narrativegraphs.nlp.triplets.common import Triplet, TripletExtractor

_logger = logging.getLogger("narrativegraphs.nlp.extraction")

_SYSTEM_PROMPT = """\
You extract subject-predicate-object semantic triplets from text.

Rules:
- Copy the subject, predicate and object verbatim from the text. Never \
paraphrase, translate, inflect or normalize them, and never introduce words \
that are not in the text. They are matched back against the source text \
character by character.
- Keep each part short: a subject or object is a noun phrase without its \
modifying clauses, a predicate is the verb and, where the relation needs it, \
its particle or preposition.
- The three parts must be non-overlapping spans of the same sentence.
- Quote that whole sentence verbatim as the evidence.
- Resolve pronouns to the entity they refer to only if that entity is named \
elsewhere in the same sentence; otherwise skip the triplet.
- Extracting nothing is a valid answer for a document that holds no such relations.

The user's extraction instructions:
{instructions}
"""


class _ExtractedTriplet(BaseModel):
    """One triplet as the model is asked to report it."""

    model_config = ConfigDict(extra="forbid")

    subject: str
    predicate: str
    object: str
    evidence: str


class _TripletResponse(BaseModel):
    """The whole response. Only used to derive the schema that constrains it."""

    model_config = ConfigDict(extra="forbid")

    triplets: list[_ExtractedTriplet]


_SCHEMA = json_schema_of(_TripletResponse)


@dataclass
class AlignmentStats:
    """How much of what the model returned could be located in the text.

    A triplet whose parts cannot be found verbatim is dropped, which is what
    keeps hallucinated and paraphrased spans out of the graph. The drop rate
    is therefore a quality signal about the instructions and the model: a few
    percent is normal, a large fraction means the model is paraphrasing and
    the extraction is not measuring what it appears to.
    """

    returned: int = 0
    kept: int = 0

    @property
    def dropped(self) -> int:
        return self.returned - self.kept

    @property
    def drop_rate(self) -> float:
        return self.dropped / self.returned if self.returned else 0.0

    def summary(self) -> str:
        return (
            f"{self.kept}/{self.returned} triplets aligned to the text "
            f"({self.drop_rate:.1%} dropped)"
        )


class _LlmTripletExtractor(TripletExtractor):
    """Shared prompt, schema and span alignment for the LLM triplet extractors.

    Subclasses differ only in how they get responses back: immediately, or
    through the Message Batches API.

    Since the rest of the package addresses entities by their position in the
    document, every returned surface form is aligned back to the source text,
    and triplets whose parts cannot be found there are dropped.
    """

    def __init__(self, instructions: str, llm: LlmClient = None):
        """
        Args:
            instructions: a short description of the entities and relations to
                extract, e.g. "extract relations between characters and the
                places they travel to"
            llm: which model to ask; defaults to Claude via `AnthropicClient`.
                Pass `OpenAiCompatibleClient(...)` for OpenAI or any server
                speaking its chat-completions API.
        """
        if not instructions or not instructions.strip():
            raise ValueError(
                "instructions must describe which entities and relations to extract"
            )
        self.instructions = instructions.strip()
        self._llm = llm if llm is not None else AnthropicClient()
        self._system_prompt = _SYSTEM_PROMPT.format(instructions=self.instructions)
        self.alignment_stats = AlignmentStats()
        # extract() runs concurrently across documents.
        self._stats_lock = threading.Lock()

    def _triplets_from_response(
        self, text: str, response: Optional[dict[str, Any]]
    ) -> list[Triplet]:
        """Align one document's extracted triplets back onto its text."""
        if response is None:
            return []

        returned = response.get("triplets") or []
        triplets = []
        for item in returned:
            extracted = _validated(item)
            if extracted is None:
                continue
            triplet = self._to_triplet(text, extracted)
            if triplet is not None:
                triplets.append(triplet)

        with self._stats_lock:
            self.alignment_stats.returned += len(returned)
            self.alignment_stats.kept += len(triplets)
        return triplets

    def _log_alignment_stats(self) -> None:
        stats = self.alignment_stats
        if not stats.returned:
            return
        message = "Span alignment: %s"
        if stats.drop_rate > 0.2:
            _logger.warning(
                message + " — a large fraction of what the model returned could not "
                "be found in the text; check that the instructions ask for verbatim "
                "spans",
                stats.summary(),
            )
        else:
            _logger.info(message, stats.summary())

    def _to_triplet(
        self, text: str, extracted: "_ExtractedTriplet"
    ) -> Optional[Triplet]:
        parts = [extracted.subject, extracted.predicate, extracted.object]
        if not all(part.strip() for part in parts):
            _logger.debug("Dropping triplet with an empty part: %s", extracted)
            return None

        evidence = align_span(text, extracted.evidence)
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
        llm: LlmClient = None,
        max_concurrent_requests: int = 4,
    ):
        """
        Args:
            instructions: a short description of the entities and relations to
                extract
            llm: which model to ask; defaults to Claude
            max_concurrent_requests: number of documents in flight at a time
        """
        super().__init__(instructions, llm=llm)
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
        self._log_alignment_stats()


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
        triplets = extractor.collect(batch_ids, docs)
        ng = NarrativeGraph().fit(docs, triplets=triplets)
    """

    def __init__(
        self,
        instructions: str,
        llm: BatchLlmClient = None,
        chunk_size: int = DEFAULT_BATCH_CHUNK_SIZE,
        poll_interval: float = 60.0,
    ):
        """
        Args:
            instructions: a short description of the entities and relations to
                extract
            llm: which model to ask; must be able to queue work
                asynchronously, which today means Claude via `AnthropicClient`
            chunk_size: documents per batch; smaller chunks mean results start
                landing sooner
            poll_interval: seconds between checks on a running batch

        Raises:
            TypeError: the client cannot queue work asynchronously. Most
                OpenAI-compatible servers have no batch API at all; use
                `LlmTripletExtractor` with those.
        """
        super().__init__(instructions, llm=llm)
        if not isinstance(self._llm, BatchLlmClient):
            raise TypeError(
                f"{type(self._llm).__name__} cannot process batches. Use "
                "LlmTripletExtractor for immediate requests instead."
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
            self._system_prompt, prompts, _SCHEMA, self.chunk_size
        )

    def collect(
        self, batch_ids: Iterable[str], texts: Iterable[str]
    ) -> list[list[Triplet]]:
        """Wait for submitted batches and return one list of triplets per document.

        Chunks end in whatever order the provider finishes them, so results are
        put back into the order of `texts` here. That is also the shape
        `NarrativeGraph.fit` takes as `triplets=` and `Pipeline.run` as
        `annotations=`. A document that was never submitted, or whose request
        errored or expired, comes back as an empty list rather than being
        missing, so every document is accounted for.

        Args:
            batch_ids: the IDs returned by `submit`
            texts: the same documents, in the same order, that were submitted;
                needed because aligning a triplet requires its source text

        Returns:
            one list of triplets per document, in the order of `texts`
        """
        texts = list(texts)
        collected: list[list[Triplet]] = [[] for _ in texts]
        for index, triplets in self._collect_as_they_land(batch_ids, texts):
            collected[index] = triplets
        return collected

    def _collect_as_they_land(
        self, batch_ids: Iterable[str], texts: list[str]
    ) -> Generator[tuple[int, list[Triplet]], None, None]:
        """Yield (index, triplets) as each chunk ends, in whatever order that is."""
        for custom_id, response in self._llm.collect_batches(
            batch_ids, self.poll_interval
        ):
            index = _index_from_custom_id(custom_id, len(texts))
            if index is None:
                _logger.warning("Ignoring result with unexpected id %r", custom_id)
                continue
            yield index, self._triplets_from_response(texts[index], response)
        self._log_alignment_stats()

    def extract(self, text: str) -> list[Triplet]:
        """Extract from a single document by submitting a batch of one.

        Batching a lone document buys nothing but the lower price, and still
        waits for the batch to end. Prefer `batch_extract`.
        """
        for triplets in self.batch_extract([text]):
            return triplets
        return []

    def batch_extract(
        self, texts: Iterable[str], n_cpu: int = 1, **kwargs
    ) -> Generator[list[Triplet], None, None]:
        """Submit every document, wait for the batches and yield them in order.

        This blocks until the whole run has ended, which for a large corpus may
        be hours. `submit` and `collect` split the same work in two, so that the
        wait can be sat out with the machine off.

        Args:
            texts: an iterable of raw text strings
            n_cpu: ignored; the work happens on the provider's infrastructure
            **kwargs: unused

        Returns:
            yields triplets per text in the same order as the texts iterable
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


def _validated(item: Any) -> Optional[_ExtractedTriplet]:
    """Check one triplet against the schema the model was given.

    Validated per item rather than per response so that one malformed triplet
    costs only itself, not the whole document.
    """
    try:
        return _ExtractedTriplet.model_validate(item)
    except ValidationError as e:
        _logger.debug("Dropping triplet that does not match the schema: %s", e)
        return None


def _overlapping(spans: list[Span]) -> bool:
    ordered = sorted(spans)
    return any(
        current[1] > following[0] for current, following in zip(ordered, ordered[1:])
    )
