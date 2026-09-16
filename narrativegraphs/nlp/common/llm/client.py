"""The model- and server-agnostic interface for LLM-backed pipeline steps.

Pipeline components depend on this and nothing else, so a step works against
any provider without knowing which one it has. Implementations live beside
this module, one per provider family, and keep their own quirks to themselves.

Structured output is the only thing providers genuinely disagree about, so it
is the only thing this abstracts. An implementation takes a system prompt, a
user prompt and a JSON schema, and returns the object the model produced.
"""

import json
import re
from abc import ABC, abstractmethod
from typing import Any, Generator, Iterable, Optional

from pydantic import BaseModel

JsonSchema = dict[str, Any]

# Code fences that smaller local models like to wrap JSON in, despite being
# asked for a schema. The closing fence is optional: a response cut off at the
# token cap never gets to write it.
_FENCE = re.compile(r"^\s*```(?:json)?\s*(.*?)(?:\s*```)?\s*$", re.DOTALL)


def parse_json_object(text: str) -> Optional[dict[str, Any]]:
    """Read a model's response text as a JSON object.

    Three things go wrong often enough to handle once here rather than in each
    provider: a server honouring the schema returns bare JSON, smaller local
    models wrap it in a code fence even when told not to, and a response that
    ran into the token cap stops mid-object. The last is recovered up to the
    last element that was complete, which keeps the work the model had already
    done instead of dropping the document over its final, half-written item.

    Returns:
        the object, or None if nothing usable could be read
    """
    for candidate in (text.strip(), _unfenced(text)):
        if candidate is None:
            continue
        try:
            parsed = json.loads(candidate)
        except json.JSONDecodeError:
            parsed = _parse_truncated(candidate)
        if isinstance(parsed, dict):
            return parsed
    return None


def _unfenced(text: str) -> Optional[str]:
    fenced = _FENCE.match(text)
    return fenced.group(1) if fenced else None


def _parse_truncated(text: str) -> Optional[Any]:
    """Parse as much of a cut-off JSON document as is syntactically complete."""
    closable = _close_at_last_complete_element(text)
    if closable is None:
        return None
    try:
        return json.loads(closable)
    except json.JSONDecodeError:
        return None


def _close_at_last_complete_element(text: str) -> Optional[str]:
    """Trim to the last finished element and close the brackets still open.

    An element is finished where a comma or a closing bracket follows it, so
    the brackets open at that point — recorded as they were then, not as they
    are at the end of the text — are what has to be closed again.
    """
    open_brackets: list[str] = []
    cut_at: Optional[tuple[int, tuple[str, ...]]] = None
    in_string = False
    escaped = False

    for index, char in enumerate(text):
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
        elif char in "[{":
            open_brackets.append("]" if char == "[" else "}")
        elif char in "]}":
            if not open_brackets:
                return None
            open_brackets.pop()
            cut_at = (index + 1, tuple(open_brackets))
        elif char == "," and open_brackets:
            cut_at = (index, tuple(open_brackets))

    if not open_brackets or cut_at is None:
        # Nothing was cut off, or nothing was finished before the cut.
        return None
    index, still_open = cut_at
    return text[:index] + "".join(reversed(still_open))


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
