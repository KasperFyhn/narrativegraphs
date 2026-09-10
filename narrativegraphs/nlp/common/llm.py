"""Shared building blocks for LLM-based pipeline steps.

Two concerns live here, both of which are independent of *which* pipeline step is
being implemented with an LLM:

1. Talking to the model (`LlmJsonClient`): a thin wrapper around the Anthropic
   Messages API that always asks for a JSON object matching a given schema.
2. Getting back into the text (`align_span` and friends): an LLM returns
   strings, but the rest of the package works on character offsets into the
   source document, so returned surface forms must be located in the text again.
"""

import json
import logging
import re
from collections import deque
from concurrent.futures import ThreadPoolExecutor
from itertools import islice
from typing import Any, Callable, Generator, Iterable, Optional, TypeVar

_logger = logging.getLogger("narrativegraphs.nlp.llm")

DEFAULT_MODEL = "claude-opus-5"

Span = tuple[int, int]

_T = TypeVar("_T")
_R = TypeVar("_R")

_SENTINEL = object()


class LlmError(RuntimeError):
    """Raised when the model could not be queried in a way worth retrying."""


class LlmJsonClient:
    """Requests JSON objects from Claude according to a JSON schema.

    Structured outputs (`output_config.format`) guarantee that the response is a
    single text block containing a JSON object valid against the schema, so no
    prompt-level pleading for "valid JSON only" is needed.

    Requires optional dependency: anthropic>=1.0.0
    """

    def __init__(
        self,
        model: str = DEFAULT_MODEL,
        effort: str = "low",
        max_tokens: int = 16000,
        client: Any = None,
    ):
        """
        Args:
            model: Claude model ID; `claude-sonnet-5` or `claude-haiku-4-5` are
                cheaper alternatives for large corpora
            effort: thinking/token effort, one of "low", "medium", "high",
                "xhigh", "max"; extraction against a short instruction is a
                bounded task run at corpus scale, hence the low default
            max_tokens: cap on the response; long documents yield long JSON, so
                raise this rather than lowering it
            client: a pre-configured `anthropic.Anthropic` instance; if omitted,
                one is created lazily, resolving credentials from the
                environment (`ANTHROPIC_API_KEY` et al.)
        """
        self.model = model
        self.effort = effort
        self.max_tokens = max_tokens
        self._client = client

    @property
    def client(self) -> Any:
        if self._client is None:
            try:
                import anthropic
            except ImportError:
                raise ImportError(
                    "anthropic is required for LLM-based pipeline steps. "
                    "Install it with: pip install 'narrativegraphs[llm-anthropic]'"
                )
            self._client = anthropic.Anthropic()
        return self._client

    def request_json(
        self, system_prompt: str, user_prompt: str, schema: dict[str, Any]
    ) -> Optional[dict[str, Any]]:
        """Ask for a single JSON object matching `schema`.

        Args:
            system_prompt: the stable part of the prompt, i.e. the task
                definition and the user's extraction instructions
            user_prompt: the per-request part, i.e. the document to work on
            schema: a JSON schema describing the expected object

        Returns:
            the parsed object, or None if the model declined or returned
            something unusable; systematic failures (bad credentials, malformed
            requests) raise instead, as retrying those on the next document
            would only produce an empty graph the slow way
        """
        response = self._create_message(system_prompt, user_prompt, schema)
        if response is None:
            return None

        if getattr(response, "stop_reason", None) == "refusal":
            details = getattr(response, "stop_details", None)
            _logger.warning(
                "Model declined to process a document (category: %s)",
                getattr(details, "category", None),
            )
            return None

        text = next(
            (b.text for b in response.content if getattr(b, "type", None) == "text"),
            None,
        )
        if text is None:
            _logger.warning("No text block in model response; skipping document")
            return None

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            if getattr(response, "stop_reason", None) == "max_tokens":
                _logger.warning(
                    "Response hit the %d token cap and was cut off; "
                    "raise max_tokens or shorten the documents",
                    self.max_tokens,
                )
            else:
                _logger.warning("Could not parse model response as JSON")
            return None

    def _create_message(
        self, system_prompt: str, user_prompt: str, schema: dict[str, Any]
    ) -> Any:
        # Resolved outside the try block so that a missing dependency surfaces
        # as an ImportError rather than as an empty graph.
        client = self.client
        try:
            return client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                system=[
                    {
                        "type": "text",
                        "text": system_prompt,
                        "cache_control": {"type": "ephemeral"},
                    }
                ],
                messages=[{"role": "user", "content": user_prompt}],
                output_config={
                    "effort": self.effort,
                    "format": {"type": "json_schema", "schema": schema},
                },
            )
        except Exception as e:
            if _is_systematic_error(e):
                raise LlmError(f"Cannot query the model: {e}") from e
            _logger.warning("Model request failed, skipping document: %s", e)
            return None


def _is_systematic_error(error: Exception) -> bool:
    """Tell configuration errors from transient ones.

    The SDK already retries rate limits and server errors, so anything reaching
    us is either a per-document hiccup or a setup problem that every subsequent
    document would hit as well.
    """
    try:
        import anthropic
    except ImportError:
        return False
    return isinstance(
        error,
        (
            anthropic.AuthenticationError,
            anthropic.PermissionDeniedError,
            anthropic.BadRequestError,
            anthropic.NotFoundError,
        ),
    )


def map_ordered(
    fn: Callable[[_T], _R], items: Iterable[_T], max_workers: int = 4
) -> Generator[_R, None, None]:
    """Apply `fn` concurrently, yielding results in input order.

    LLM calls are I/O-bound, so threads rather than processes. Only
    `max_workers` items are pulled from `items` ahead of the results being
    consumed, which keeps generator inputs lazy.
    """
    if max_workers <= 1:
        for item in items:
            yield fn(item)
        return

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        iterator = iter(items)
        pending = deque(
            executor.submit(fn, item) for item in islice(iterator, max_workers)
        )
        while pending:
            yield pending.popleft().result()
            next_item = next(iterator, _SENTINEL)
            if next_item is not _SENTINEL:
                pending.append(executor.submit(fn, next_item))


def align_span(
    text: str, surface: str, start: int = 0, end: Optional[int] = None
) -> Optional[Span]:
    """Locate `surface` in `text[start:end]` and return its character offsets.

    Models reproduce surface forms with small deviations — casing normalized,
    line breaks collapsed into spaces — so matching is attempted in decreasing
    order of strictness: verbatim, case-insensitive, then whitespace-flexible.

    Returns:
        (start_char, end_char) of the first match, or None if there is none
    """
    if not surface or not surface.strip():
        return None
    if end is None:
        end = len(text)
    if start >= end:
        return None

    found = text.find(surface, start, end)
    if found != -1:
        return found, found + len(surface)

    pattern = re.compile(
        r"\s+".join(re.escape(token) for token in surface.split()), re.IGNORECASE
    )
    match = pattern.search(text, start, end)
    if match is not None:
        return match.start(), match.end()

    return None


def align_sequence(
    text: str, surfaces: list[str], window: Optional[Span] = None
) -> Optional[list[Span]]:
    """Locate several surface forms that are expected to appear in order.

    A document usually mentions the same entity more than once, so anchoring on
    the first occurrence of each part in isolation tends to stitch together
    spans from unrelated sentences. Instead, each part is searched for after the
    end of the previous one, first inside `window` (typically the sentence the
    model quoted as evidence) and then in the document as a whole.

    Returns:
        one (start_char, end_char) per surface form, or None if any of them
        could not be located at all
    """
    windows = [window] if window is not None else []
    windows.append((0, len(text)))

    for start, end in windows:
        spans = _align_in_order(text, surfaces, start, end)
        if spans is None:
            # The parts may all be there but not in the order the model listed
            # them, as in passive constructions and inversions.
            spans = _align_independently(text, surfaces, start, end)
        if spans is not None:
            return spans

    return None


def _align_in_order(
    text: str, surfaces: list[str], start: int, end: int
) -> Optional[list[Span]]:
    spans = []
    cursor = start
    for surface in surfaces:
        span = align_span(text, surface, cursor, end)
        if span is None:
            return None
        spans.append(span)
        cursor = span[1]
    return spans


def _align_independently(
    text: str, surfaces: list[str], start: int, end: int
) -> Optional[list[Span]]:
    spans = [align_span(text, surface, start, end) for surface in surfaces]
    if any(span is None for span in spans):
        return None
    return spans
