"""The OpenAI-compatible adapter.

Exercised with an injected fake client, so the SDK need not be installed and
nothing reaches the network. What is under test is the translation: one schema
in, one dict out, whatever envelope the server wants in between.
"""

import json
import unittest
from types import SimpleNamespace

from narrativegraphs.nlp.common.llm import LlmError, OpenAiCompatibleClient
from narrativegraphs.nlp.triplets.llm import (
    LlmBatchTripletExtractor,
    LlmTripletExtractor,
)

SCHEMA = {
    "type": "object",
    "properties": {"triplets": {"type": "array", "items": {"type": "object"}}},
    "required": ["triplets"],
    "additionalProperties": False,
}


class FakeCompletions:
    def __init__(self, content, finish_reason="stop", refusal=None, error=None):
        self.content = content
        self.finish_reason = finish_reason
        self.refusal = refusal
        self.error = error
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        if self.error is not None:
            raise self.error
        return SimpleNamespace(
            choices=[
                SimpleNamespace(
                    message=SimpleNamespace(content=self.content, refusal=self.refusal),
                    finish_reason=self.finish_reason,
                )
            ]
        )


class FakeOpenAiClient:
    def __init__(self, content=None, **kwargs):
        self.completions = FakeCompletions(content, **kwargs)
        self.chat = SimpleNamespace(completions=self.completions)


class _StatusError(Exception):
    """An SDK error as the client sees it: an exception carrying a status."""

    def __init__(self, status_code):
        super().__init__(f"HTTP {status_code}")
        self.status_code = status_code


def make_client(content=None, **response_kwargs):
    fake = FakeOpenAiClient(content, **response_kwargs)
    return OpenAiCompatibleClient("llama3.1:8b", client=fake)


class TestRequest(unittest.TestCase):
    def test_constrains_output_with_a_json_schema(self):
        client = make_client('{"triplets": []}')

        result = client.request_json("be precise", "the document", SCHEMA)

        self.assertEqual({"triplets": []}, result)
        (call,) = client.client.completions.calls
        self.assertEqual("llama3.1:8b", call["model"])
        self.assertEqual(
            {"role": "system", "content": "be precise"}, call["messages"][0]
        )
        self.assertEqual(
            {"role": "user", "content": "the document"}, call["messages"][1]
        )
        self.assertEqual("json_schema", call["response_format"]["type"])
        self.assertEqual(SCHEMA, call["response_format"]["json_schema"]["schema"])

    def test_strict_is_off_by_default_for_compatibility(self):
        client = make_client('{"triplets": []}')
        client.request_json("s", "u", SCHEMA)

        (call,) = client.client.completions.calls
        self.assertFalse(call["response_format"]["json_schema"]["strict"])

    def test_strict_can_be_turned_on(self):
        fake = FakeOpenAiClient('{"triplets": []}')
        client = OpenAiCompatibleClient("gpt-4.1", client=fake, strict=True)

        client.request_json("s", "u", SCHEMA)

        (call,) = fake.completions.calls
        self.assertTrue(call["response_format"]["json_schema"]["strict"])

    def test_temperature_defaults_to_deterministic(self):
        client = make_client('{"triplets": []}')
        client.request_json("s", "u", SCHEMA)

        (call,) = client.client.completions.calls
        self.assertEqual(0.0, call["temperature"])


class TestSloppyOutput(unittest.TestCase):
    """Small local models wrap JSON even when given a schema."""

    def test_recovers_json_from_a_fenced_block(self):
        client = make_client('```json\n{"triplets": []}\n```')

        self.assertEqual({"triplets": []}, client.request_json("s", "u", SCHEMA))

    def test_recovers_json_from_a_fence_without_a_language(self):
        client = make_client('```\n{"triplets": []}\n```')

        self.assertEqual({"triplets": []}, client.request_json("s", "u", SCHEMA))

    def test_tolerates_surrounding_whitespace(self):
        client = make_client('  {"triplets": []}  ')

        self.assertEqual({"triplets": []}, client.request_json("s", "u", SCHEMA))


class TestFailures(unittest.TestCase):
    def test_refusal_yields_nothing(self):
        client = make_client(None, refusal="I can't help with that")

        self.assertIsNone(client.request_json("s", "u", SCHEMA))

    def test_empty_content_yields_nothing(self):
        client = make_client(None, finish_reason="length")

        self.assertIsNone(client.request_json("s", "u", SCHEMA))

    def test_unparseable_content_yields_nothing(self):
        client = make_client("I am afraid I cannot do that.")

        self.assertIsNone(client.request_json("s", "u", SCHEMA))

    def test_a_json_array_is_not_an_object(self):
        client = make_client('["not", "an", "object"]')

        self.assertIsNone(client.request_json("s", "u", SCHEMA))

    def test_an_unreachable_server_yields_nothing(self):
        """A local server that blinked: worth skipping the document over."""
        import httpx
        import openai

        client = make_client(
            error=openai.APIConnectionError(
                request=httpx.Request("POST", "http://localhost:11434/v1/chat")
            )
        )

        self.assertIsNone(client.request_json("s", "u", SCHEMA))

    def test_a_response_cut_off_at_the_cap_keeps_what_was_complete(self):
        """A reasoning model spends the same token budget on its thinking."""
        text = "Frodo carried the ring. Sam cooked potatoes."
        truncated = (
            '{"triplets": ['
            + json.dumps(
                {
                    "subject": "Frodo",
                    "predicate": "carried",
                    "object": "the ring",
                    "evidence": "Frodo carried the ring.",
                }
            )
            + ', {"subject": "Sam", "predicate": "coo'
        )
        fake = FakeOpenAiClient(truncated, finish_reason="length")
        extractor = LlmTripletExtractor(
            "Extract relations.", llm=OpenAiCompatibleClient("m", client=fake)
        )

        (triplet,) = extractor.extract(text)

        self.assertEqual("Frodo", triplet.subj.text)

    def test_a_cut_off_response_with_nothing_complete_yields_nothing(self):
        client = make_client('{"triplets": [{"subject": "Fro', finish_reason="length")

        self.assertIsNone(client.request_json("s", "u", SCHEMA))

    def test_an_overloaded_server_yields_nothing(self):
        client = make_client(error=_StatusError(503))

        self.assertIsNone(client.request_json("s", "u", SCHEMA))


class TestWithTheExtractor(unittest.TestCase):
    """The whole point: a pipeline component that does not know the provider."""

    def test_extracts_triplets_through_an_openai_compatible_server(self):
        text = "Frodo carried the ring to Mordor."
        payload = (
            '{"triplets": [{"subject": "Frodo", "predicate": "carried", '
            '"object": "the ring", "evidence": "Frodo carried the ring to Mordor."}]}'
        )
        fake = FakeOpenAiClient(payload)
        extractor = LlmTripletExtractor(
            "Extract relations between people and places.",
            llm=OpenAiCompatibleClient("llama3.1:8b", client=fake),
        )

        (triplet,) = extractor.extract(text)

        self.assertEqual("Frodo", triplet.subj.text)
        self.assertEqual((0, 5), (triplet.subj.start_char, triplet.subj.end_char))
        self.assertEqual("the ring", triplet.obj.text)

    def test_span_alignment_applies_to_any_provider(self):
        """Hallucinated spans are dropped regardless of which model produced them."""
        text = "Frodo carried the ring to Mordor."
        payload = (
            '{"triplets": [{"subject": "Sam", "predicate": "cooked", '
            '"object": "potatoes", "evidence": "Frodo carried the ring to Mordor."}]}'
        )
        fake = FakeOpenAiClient(payload)
        extractor = LlmTripletExtractor(
            "Extract relations.", llm=OpenAiCompatibleClient("m", client=fake)
        )

        self.assertEqual([], extractor.extract(text))


class TestBatchGuard(unittest.TestCase):
    def test_batch_extractor_rejects_a_client_that_cannot_batch(self):
        """Most OpenAI-compatible servers have no batch API; fail at construction."""
        with self.assertRaises(TypeError) as raised:
            LlmBatchTripletExtractor(
                "Extract relations.",
                llm=OpenAiCompatibleClient("llama3.1:8b", client=FakeOpenAiClient()),
            )

        self.assertIn("cannot process batches", str(raised.exception))


class TestErrors(unittest.TestCase):
    def test_missing_dependency_is_not_swallowed(self):
        import builtins

        client = OpenAiCompatibleClient("gpt-4.1")
        real_import = builtins.__import__

        def no_openai(name, *args, **kwargs):
            if name == "openai":
                raise ImportError("no module named openai")
            return real_import(name, *args, **kwargs)

        builtins.__import__ = no_openai
        try:
            with self.assertRaises(ImportError):
                client.request_json("s", "u", SCHEMA)
        finally:
            builtins.__import__ = real_import

    def test_llm_error_is_available_for_systematic_failures(self):
        self.assertTrue(issubclass(LlmError, RuntimeError))

    def test_unresolvable_credentials_stop_the_run(self):
        """A server that needs a key and got none must not be skipped per document."""
        client = make_client(error=TypeError("api_key client option must be set"))

        with self.assertRaises(LlmError):
            client.request_json("s", "u", SCHEMA)

    def test_an_unrecognized_failure_stops_the_run(self):
        """Anything not known to be transient is treated as a setup problem."""
        client = make_client(error=RuntimeError("something unforeseen"))

        with self.assertRaises(LlmError):
            client.request_json("s", "u", SCHEMA)


if __name__ == "__main__":
    unittest.main()
