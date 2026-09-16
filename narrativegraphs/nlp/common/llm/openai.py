"""Any server speaking the OpenAI chat-completions API.

The same adapter covers hosted OpenAI and local runtimes; only `base_url`
changes:

    OpenAI      the SDK default
    LM Studio   http://localhost:1234/v1
    Ollama      http://localhost:11434/v1
    vLLM        http://localhost:8000/v1

Everything in here is specific to that API and invisible to pipeline
components, which see only `LlmClient`.
"""

import json
import logging
import os
import re
from typing import Any, Optional

from narrativegraphs.nlp.common.llm.client import JsonSchema, LlmClient, LlmError

_logger = logging.getLogger("narrativegraphs.nlp.llm")

# The name the schema is given in the request. OpenAI requires one; it does
# not affect the object that comes back.
_SCHEMA_NAME = "extraction"

# Code fences that smaller local models like to wrap JSON in, despite being
# asked for a schema.
_FENCE = re.compile(r"^\s*```(?:json)?\s*(.*?)\s*```\s*$", re.DOTALL)


class OpenAiCompatibleClient(LlmClient):
    """Requests JSON objects from an OpenAI-compatible chat-completions server.

    Structured output uses `response_format` with a JSON schema, which local
    runtimes implement by constrained decoding.

    Args:
        model: model name as the server knows it, e.g. "gpt-4.1" or
            "llama3.1:8b"
        base_url: the server's endpoint, e.g. "http://localhost:11434/v1";
            omit for hosted OpenAI
        api_key: key; falls back to `OPENAI_API_KEY`, then to a placeholder,
            since local servers ignore it but the SDK insists on one
        temperature: sampling temperature; 0.0 for near-deterministic
            extraction
        max_tokens: cap on the response
        strict: whether to ask for strict schema adherence. Off by default
            because not every compatible server implements it; hosted OpenAI
            does, and the schemas used here are strict-compatible.
        client: a pre-configured `openai.OpenAI` instance
    """

    def __init__(
        self,
        model: str,
        base_url: str = None,
        api_key: str = None,
        temperature: float = 0.0,
        max_tokens: int = 16000,
        strict: bool = False,
        client: Any = None,
    ):
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.strict = strict
        self._base_url = base_url
        self._api_key = api_key
        self._client = client

    @property
    def client(self) -> Any:
        if self._client is None:
            try:
                from openai import OpenAI
            except ImportError:
                raise ImportError(
                    "openai is required for OpenAiCompatibleClient. It ships with "
                    "narrativegraphs; reinstall it with: pip install openai"
                )
            kwargs = {
                # Local servers ignore the key, but the SDK insists on one.
                "api_key": self._api_key
                or os.environ.get("OPENAI_API_KEY")
                or "not-needed",
            }
            if self._base_url:
                kwargs["base_url"] = self._base_url
            self._client = OpenAI(**kwargs)
        return self._client

    def request_json(
        self, system_prompt: str, user_prompt: str, schema: JsonSchema
    ) -> Optional[dict[str, Any]]:
        # Resolved outside the try block so that a missing dependency surfaces
        # as an ImportError rather than as an empty graph.
        client = self.client
        try:
            response = client.chat.completions.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": _SCHEMA_NAME,
                        "schema": schema,
                        "strict": self.strict,
                    },
                },
            )
        except Exception as e:
            if _is_transient(e):
                _logger.warning("Model request failed, skipping document: %s", e)
                return None
            raise LlmError(f"Cannot query the model: {e}") from e
        return self._parse_response(response)

    def _parse_response(self, response: Any) -> Optional[dict[str, Any]]:
        choices = getattr(response, "choices", None) or []
        if not choices:
            _logger.warning("No choices in model response; skipping document")
            return None
        choice = choices[0]

        if getattr(choice.message, "refusal", None):
            _logger.warning(
                "Model declined to process a document: %s", choice.message.refusal
            )
            return None

        content = getattr(choice.message, "content", None)
        if not content:
            # Reasoning models (Qwen3's hybrid thinking, DeepSeek-R1-style
            # servers, ...) can put the whole schema-constrained answer in a
            # separate reasoning field and leave `content` empty, even though
            # the request finished normally.
            content = getattr(choice.message, "reasoning_content", None)
            if content:
                _logger.debug(
                    "Model left content empty; using reasoning_content instead"
                )
        if not content:
            _logger.warning(
                "Empty model response (finish_reason: %s); skipping document",
                getattr(choice, "finish_reason", None),
            )
            return None

        parsed = _parse_json_object(content)
        if parsed is None:
            if getattr(choice, "finish_reason", None) == "length":
                _logger.warning(
                    "Response hit the %d token cap and was cut off; "
                    "raise max_tokens or shorten the documents",
                    self.max_tokens,
                )
            else:
                _logger.warning("Could not parse model response as JSON")
        return parsed


def _parse_json_object(content: str) -> Optional[dict[str, Any]]:
    """Parse the response text into an object.

    A server that honours the schema returns bare JSON; smaller local models
    wrap it in a code fence even when told not to, so that is stripped too.
    """
    candidates = [content.strip()]
    fenced = _FENCE.match(content)
    if fenced:
        candidates.append(fenced.group(1))

    for candidate in candidates:
        try:
            parsed = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict):
            return parsed
    return None


def _is_transient(error: Exception) -> bool:
    """Tell a per-document hiccup from a setup problem.

    As in the Anthropic client: only what is known to be worth skipping a
    document over is transient, so a misconfiguration stops the run instead of
    being swallowed once per document.
    """
    try:
        import openai
    except ImportError:
        return False
    if isinstance(error, (openai.APIConnectionError, openai.RateLimitError)):
        return True
    status = getattr(error, "status_code", None)
    return isinstance(status, int) and status >= 500
