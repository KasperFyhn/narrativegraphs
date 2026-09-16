"""The model- and server-agnostic interface for LLM-backed pipeline steps.

Pipeline components depend on this and nothing else, so a step works against
any provider without knowing which one it has. Implementations live beside
this module, one per provider family, and keep their own quirks to themselves.

Structured output is the only thing providers genuinely disagree about, so it
is the only thing this abstracts. An implementation takes a system prompt, a
user prompt and a JSON schema, and returns the object the model produced.
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Generator, Iterable, Optional

from pydantic import BaseModel

JsonSchema = dict[str, Any]

# INFO logging for each 200 is a bit excessive
logging.getLogger("httpx2").setLevel(logging.WARNING)


def json_schema_of(model: type[BaseModel]) -> JsonSchema:
    """Derive a provider-ready JSON schema from a Pydantic model.

    Defining the expected response as a model keeps the schema sent to the
    model and the validation of what comes back from drifting apart.

    Pydantic expresses nested models as `$defs` and `$ref`. Not every provider
    resolves those, and few local servers doing constrained decoding do, so
    the definitions are inlined here. Recursive models would not survive that
    and are not used.
    """
    schema = model.model_json_schema()
    definitions = schema.pop("$defs", {})
    return _inline_refs(schema, definitions)


def _inline_refs(node: Any, definitions: dict[str, Any]) -> Any:
    if isinstance(node, dict):
        reference = node.get("$ref")
        if reference is not None:
            resolved = dict(definitions[reference.rsplit("/", 1)[-1]])
            resolved.update({k: v for k, v in node.items() if k != "$ref"})
            return _inline_refs(resolved, definitions)
        return {key: _inline_refs(value, definitions) for key, value in node.items()}
    if isinstance(node, list):
        return [_inline_refs(item, definitions) for item in node]
    return node


class LlmError(RuntimeError):
    """Raised when a model cannot be queried in a way worth retrying.

    Bad credentials and malformed requests are the cases that matter: every
    later document would fail the same way, so failing loudly beats spending
    an hour building an empty graph.
    """


class LlmClient(ABC):
    """Returns JSON objects conforming to a schema, from some model."""

    @abstractmethod
    def request_json(
        self, system_prompt: str, user_prompt: str, schema: JsonSchema
    ) -> Optional[dict[str, Any]]:
        """Ask for a single JSON object matching `schema`.

        Args:
            system_prompt: the stable part of the prompt, i.e. the task
                definition and the user's extraction instructions
            user_prompt: the per-request part, i.e. the document to work on
            schema: a JSON schema describing the expected object

        Returns:
            the parsed object, or None if the model declined or returned
            something unusable — a document that produces nothing should not
            take the rest of the corpus down with it

        Raises:
            LlmError: the model cannot be queried at all
        """


class BatchLlmClient(LlmClient):
    """An `LlmClient` that can also queue requests for asynchronous processing.

    Batch APIs are cheaper but answer in their own time and only in bulk, and
    they are far from universal — most OpenAI-compatible servers have nothing
    of the kind. Steps that want batching require this narrower interface, so
    asking for it from a provider that cannot do it fails at construction
    rather than halfway through a corpus.
    """

    @abstractmethod
    def submit_batches(
        self,
        system_prompt: str,
        prompts: Iterable[tuple[str, str]],
        schema: JsonSchema,
        chunk_size: int,
    ) -> list[str]:
        """Send prompts off for processing without waiting.

        Args:
            system_prompt: the stable part of the prompt
            prompts: (custom_id, user_prompt) pairs; the custom_id is what
                identifies a result on the way back
            schema: a JSON schema describing the expected object
            chunk_size: requests per batch

        Returns:
            the ID of each submitted batch, in submission order
        """

    @abstractmethod
    def collect_batches(
        self, batch_ids: Iterable[str], poll_interval: float
    ) -> Generator[tuple[str, Optional[dict[str, Any]]], None, None]:
        """Wait for submitted batches and yield their results.

        Args:
            batch_ids: IDs returned by `submit_batches`
            poll_interval: seconds between status checks

        Returns:
            yields (custom_id, parsed object) pairs in whatever order they
            come back; the object is None for a request that failed
        """
