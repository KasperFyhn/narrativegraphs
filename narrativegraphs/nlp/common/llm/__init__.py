"""Shared building blocks for LLM-based pipeline steps.

Three layers, so that a pipeline component never needs to know which provider
it is talking to:

1. The pipeline component itself, e.g. `LlmTripletExtractor`. It builds the
   prompt and schema for its task and aligns the answer back onto the text.
2. `LlmClient` (`client.py`): the model- and server-agnostic interface. Takes
   a system prompt, a user prompt and a JSON schema; returns the object the
   model produced. `BatchLlmClient` narrows it to providers that can also
   queue work asynchronously.
3. The implementations, one per provider family — `AnthropicClient` and
   `OpenAiCompatibleClient` — each keeping its own request envelope, response
   shape and error taxonomy to itself.

`alignment` and `concurrency` are provider-neutral helpers for layer 1.
"""

from narrativegraphs.nlp.common.llm.alignment import (
    Span,
    align_sequence,
    align_span,
)
from narrativegraphs.nlp.common.llm.anthropic import (
    DEFAULT_MODEL,
    AnthropicClient,
)
from narrativegraphs.nlp.common.llm.client import (
    BatchLlmClient,
    JsonSchema,
    LlmClient,
    LlmError,
    json_schema_of,
)
from narrativegraphs.nlp.common.llm.concurrency import map_completed, map_ordered
from narrativegraphs.nlp.common.llm.openai import OpenAiCompatibleClient

# Requests per batch. A batch yields nothing until it has ended in full, so
# smaller chunks trade a little overhead for results that start landing sooner.
DEFAULT_BATCH_CHUNK_SIZE = 500

__all__ = [
    "LlmClient",
    "BatchLlmClient",
    "LlmError",
    "JsonSchema",
    "json_schema_of",
    "AnthropicClient",
    "OpenAiCompatibleClient",
    "DEFAULT_MODEL",
    "DEFAULT_BATCH_CHUNK_SIZE",
    "Span",
    "align_span",
    "align_sequence",
    "map_ordered",
    "map_completed",
]
