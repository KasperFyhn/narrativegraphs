"""Claude, through the Anthropic API.

Everything in here is specific to that API and invisible to pipeline
components, which see only `LlmClient`.
"""

import json
import logging
import time
from typing import Any, Generator, Iterable, Optional

from narrativegraphs.nlp.common.llm.client import (
    BatchLlmClient,
    JsonSchema,
    LlmError,
)

_logger = logging.getLogger("narrativegraphs.nlp.llm")

DEFAULT_MODEL = "claude-opus-5"


class AnthropicClient(BatchLlmClient):
    """Requests JSON objects from Claude, immediately or in batches.

    Structured outputs (`output_config.format`) guarantee that the response is
    a single text block containing a JSON object valid against the schema, so
    there is no prompt-level pleading for "valid JSON only" and no parsing of
    prose.

    Requires optional dependency: anthropic>=1.0.0

    Args:
        model: Claude model ID; `claude-sonnet-5` or `claude-haiku-4-5` are
            cheaper alternatives for large corpora
        effort: thinking/token effort, one of "low", "medium", "high",
            "xhigh", "max"; extraction against a short instruction is a
            bounded task run at corpus scale, hence the low default
        max_tokens: cap on the response; long documents yield long JSON, so
            raise this rather than lowering it
        client: a pre-configured `anthropic.Anthropic` instance; if omitted,
            one is created lazily, resolving credentials from the environment
            (`ANTHROPIC_API_KEY` et al.)
    """

    def __init__(
        self,
        model: str = DEFAULT_MODEL,
        effort: str = "low",
        max_tokens: int = 16000,
        client: Any = None,
    ):
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
                    "anthropic is required for AnthropicClient. "
                    "Install it with: pip install 'narrativegraphs[llm-anthropic]'"
                )
            self._client = anthropic.Anthropic()
        return self._client

    def request_json(
        self, system_prompt: str, user_prompt: str, schema: JsonSchema
    ) -> Optional[dict[str, Any]]:
        # Resolved outside the try block so that a missing dependency surfaces
        # as an ImportError rather than as an empty graph.
        client = self.client
        try:
            message = client.messages.create(
                **self._message_params(system_prompt, user_prompt, schema)
            )
        except Exception as e:
            if _is_systematic_error(e):
                raise LlmError(f"Cannot query the model: {e}") from e
            _logger.warning("Model request failed, skipping document: %s", e)
            return None
        return self._parse_message(message)

    def submit_batches(
        self,
        system_prompt: str,
        prompts: Iterable[tuple[str, str]],
        schema: JsonSchema,
        chunk_size: int,
    ) -> list[str]:
        """Queue prompts on the Message Batches API, at half the price.

        Results stay retrievable for 29 days, so the returned IDs can be
        written down, the machine turned off, and the results collected
        another day.
        """
        client = self.client
        batch_ids = []
        for chunk in _chunked(prompts, chunk_size):
            # Plain dicts: the SDK's Request/MessageCreateParamsNonStreaming
            # are TypedDicts, so these are the same objects on the wire.
            requests = [
                {
                    "custom_id": custom_id,
                    "params": self._message_params(system_prompt, prompt, schema),
                }
                for custom_id, prompt in chunk
            ]
            try:
                batch = client.messages.batches.create(requests=requests)
            except Exception as e:
                raise LlmError(f"Could not submit batch: {e}") from e
            _logger.info("Submitted batch %s with %d requests", batch.id, len(requests))
            batch_ids.append(batch.id)
        return batch_ids

    def collect_batches(
        self, batch_ids: Iterable[str], poll_interval: float = 60.0
    ) -> Generator[tuple[str, Optional[dict[str, Any]]], None, None]:
        """Wait for submitted batches and yield their results as each ends.

        A batch hands over nothing until it has ended in full, so results
        arrive chunk by chunk rather than document by document, and within a
        chunk in arbitrary order. Whichever batch ends first is yielded first.
        """
        client = self.client
        outstanding = list(batch_ids)
        failed = 0
        while outstanding:
            still_running = []
            for batch_id in outstanding:
                batch = client.messages.batches.retrieve(batch_id)
                if batch.processing_status != "ended":
                    still_running.append(batch_id)
                    continue
                for result in client.messages.batches.results(batch_id):
                    parsed = self._parse_batch_result(result)
                    if parsed is None:
                        failed += 1
                    yield result.custom_id, parsed
            outstanding = still_running
            if outstanding:
                _logger.info("Waiting on %d batch(es)", len(outstanding))
                time.sleep(poll_interval)
        if failed:
            _logger.warning("%d request(s) produced no usable result", failed)

    def _message_params(
        self, system_prompt: str, user_prompt: str, schema: JsonSchema
    ) -> dict[str, Any]:
        """Build the Messages API parameters for one document.

        Shared by the immediate and the batch path, so that a batched run is
        the same request as an immediate one.
        """
        return {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "system": [
                {
                    "type": "text",
                    "text": system_prompt,
                    "cache_control": {"type": "ephemeral"},
                }
            ],
            "messages": [{"role": "user", "content": user_prompt}],
            "output_config": {
                "effort": self.effort,
                "format": {"type": "json_schema", "schema": schema},
            },
        }

    def _parse_message(self, message: Any) -> Optional[dict[str, Any]]:
        if getattr(message, "stop_reason", None) == "refusal":
            details = getattr(message, "stop_details", None)
            _logger.warning(
                "Model declined to process a document (category: %s)",
                getattr(details, "category", None),
            )
            return None

        text = next(
            (b.text for b in message.content if getattr(b, "type", None) == "text"),
            None,
        )
        if text is None:
            _logger.warning("No text block in model response; skipping document")
            return None

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            if getattr(message, "stop_reason", None) == "max_tokens":
                _logger.warning(
                    "Response hit the %d token cap and was cut off; "
                    "raise max_tokens or shorten the documents",
                    self.max_tokens,
                )
            else:
                _logger.warning("Could not parse model response as JSON")
            return None

    def _parse_batch_result(self, result: Any) -> Optional[dict[str, Any]]:
        outcome = result.result
        if outcome.type != "succeeded":
            _logger.warning(
                "Request %s did not succeed (%s)", result.custom_id, outcome.type
            )
            return None
        return self._parse_message(outcome.message)


def _is_systematic_error(error: Exception) -> bool:
    """Tell configuration errors from transient ones.

    The SDK already retries rate limits and server errors, so anything that
    reaches us is either a per-document hiccup or a setup problem that every
    subsequent document would hit as well.
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


def _chunked(items, chunk_size):
    from itertools import islice

    iterator = iter(items)
    while chunk := list(islice(iterator, chunk_size)):
        yield chunk
