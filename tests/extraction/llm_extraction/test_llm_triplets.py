import builtins
import json
import threading
import unittest
from types import SimpleNamespace

from narrativegraphs.nlp.triplets.llm import LlmTripletExtractor


class FakeMessages:
    """Stands in for `anthropic.Anthropic().messages`."""

    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


class FakeClient:
    def __init__(self, *responses):
        self.messages = FakeMessages(responses)


class GatedClient:
    """A client whose per-document responses are released on demand.

    Lets a test decide the order in which in-flight requests complete.
    """

    def __init__(self, responses_by_text):
        self.gates = {text: threading.Event() for text in responses_by_text}
        self.messages = GatedMessages(responses_by_text, self.gates)

    def release(self, text):
        self.gates[text].set()


class GatedMessages:
    def __init__(self, responses_by_text, gates):
        self.responses_by_text = responses_by_text
        self.gates = gates
        self.calls = []

    def create(self, **kwargs):
        text = kwargs["messages"][0]["content"]
        self.calls.append(kwargs)
        if not self.gates[text].wait(timeout=10):
            raise AssertionError(f"response for {text!r} was never released")
        return self.responses_by_text[text]


def json_response(*triplets, stop_reason="end_turn"):
    payload = json.dumps({"triplets": list(triplets)})
    return SimpleNamespace(
        content=[SimpleNamespace(type="text", text=payload)],
        stop_reason=stop_reason,
        stop_details=None,
    )


def triplet_dict(subject, predicate, obj, evidence):
    return {
        "subject": subject,
        "predicate": predicate,
        "object": obj,
        "evidence": evidence,
    }


def make_extractor(*responses, **kwargs):
    return LlmTripletExtractor(
        "Extract relations between people and places.",
        client=FakeClient(*responses),
        **kwargs,
    )


def requests_made(extractor):
    """The keyword arguments of each `messages.create` call the extractor made."""
    return extractor._llm.client.messages.calls


class TestExtraction(unittest.TestCase):
    def test_aligns_verbatim_parts(self):
        text = "Frodo carried the ring to Mordor."
        extractor = make_extractor(
            json_response(triplet_dict("Frodo", "carried", "the ring", text))
        )

        (triplet,) = extractor.extract(text)

        self.assertEqual("Frodo", triplet.subj.text)
        self.assertEqual((0, 5), (triplet.subj.start_char, triplet.subj.end_char))
        self.assertEqual("carried", triplet.pred.text)
        self.assertEqual((6, 13), (triplet.pred.start_char, triplet.pred.end_char))
        self.assertEqual("the ring", triplet.obj.text)
        self.assertEqual((14, 22), (triplet.obj.start_char, triplet.obj.end_char))

    def test_context_is_the_quoted_evidence(self):
        text = "It was a long road. Frodo carried the ring to Mordor."
        extractor = make_extractor(
            json_response(
                triplet_dict(
                    "Frodo", "carried", "the ring", "Frodo carried the ring to Mordor."
                )
            )
        )

        (triplet,) = extractor.extract(text)

        self.assertEqual("Frodo carried the ring to Mordor.", triplet.context.text)
        self.assertEqual(20, triplet.context.doc_offset)

    def test_aligns_across_normalized_whitespace_and_casing(self):
        # The model collapses the line break and lowercases "the Ring".
        text = "The dark\nlord Sauron sought the Ring."
        extractor = make_extractor(
            json_response(
                triplet_dict("The dark lord Sauron", "sought", "the ring", text)
            )
        )

        (triplet,) = extractor.extract(text)

        self.assertEqual("The dark\nlord Sauron", triplet.subj.text)
        self.assertEqual("sought", triplet.pred.text)
        self.assertEqual("the Ring", triplet.obj.text)

    def test_repeated_entity_is_anchored_in_the_evidence_sentence(self):
        text = "Frodo left the Shire. Later, Frodo reached Mordor."
        extractor = make_extractor(
            json_response(
                triplet_dict(
                    "Frodo", "reached", "Mordor", "Later, Frodo reached Mordor."
                )
            )
        )

        (triplet,) = extractor.extract(text)

        # Not the first "Frodo" in the document, but the one in the evidence.
        self.assertEqual(29, triplet.subj.start_char)

    def test_out_of_order_parts_still_align(self):
        text = "The ring was carried by Frodo."
        extractor = make_extractor(
            json_response(triplet_dict("Frodo", "carried", "The ring", text))
        )

        (triplet,) = extractor.extract(text)

        self.assertEqual(24, triplet.subj.start_char)
        self.assertEqual(13, triplet.pred.start_char)
        self.assertEqual(0, triplet.obj.start_char)

    def test_drops_hallucinated_parts(self):
        text = "Frodo carried the ring to Mordor."
        extractor = make_extractor(
            json_response(
                triplet_dict("Frodo", "carried", "the ring", text),
                triplet_dict("Sam", "cooked", "potatoes", text),
            )
        )

        triplets = extractor.extract(text)

        self.assertEqual(1, len(triplets))
        self.assertEqual("Frodo", triplets[0].subj.text)

    def test_drops_paraphrased_predicate(self):
        text = "Frodo carried the ring to Mordor."
        extractor = make_extractor(
            json_response(triplet_dict("Frodo", "transported", "the ring", text))
        )

        self.assertEqual([], extractor.extract(text))

    def test_drops_triplet_with_empty_part(self):
        text = "Frodo carried the ring to Mordor."
        extractor = make_extractor(
            json_response(triplet_dict("Frodo", "  ", "the ring", text))
        )

        self.assertEqual([], extractor.extract(text))

    def test_drops_overlapping_parts(self):
        text = "Frodo carried the ring to Mordor."
        extractor = make_extractor(
            json_response(triplet_dict("Frodo carried", "carried", "the ring", text))
        )

        self.assertEqual([], extractor.extract(text))

    def test_empty_text_makes_no_request(self):
        extractor = make_extractor()

        self.assertEqual([], extractor.extract("   "))
        self.assertEqual([], requests_made(extractor))


class TestRobustness(unittest.TestCase):
    def test_refusal_yields_no_triplets(self):
        extractor = make_extractor(
            SimpleNamespace(
                content=[],
                stop_reason="refusal",
                stop_details=SimpleNamespace(category="cyber", explanation=""),
            )
        )

        self.assertEqual([], extractor.extract("Frodo carried the ring."))

    def test_unparsable_response_yields_no_triplets(self):
        extractor = make_extractor(
            SimpleNamespace(
                content=[SimpleNamespace(type="text", text="{oops")],
                stop_reason="max_tokens",
                stop_details=None,
            )
        )

        self.assertEqual([], extractor.extract("Frodo carried the ring."))

    def test_transient_failure_skips_the_document(self):
        extractor = make_extractor(RuntimeError("connection reset"))

        self.assertEqual([], extractor.extract("Frodo carried the ring."))

    def test_missing_dependency_is_not_swallowed(self):
        extractor = LlmTripletExtractor("Extract relations.")
        extractor._llm._client = None

        def no_anthropic(name, *args, **kwargs):
            if name == "anthropic":
                raise ImportError("no module named anthropic")
            return real_import(name, *args, **kwargs)

        real_import = builtins.__import__
        builtins.__import__ = no_anthropic
        try:
            with self.assertRaises(ImportError):
                extractor.extract("Frodo carried the ring.")
        finally:
            builtins.__import__ = real_import


class TestRequest(unittest.TestCase):
    def test_instructions_go_into_the_cached_system_prompt(self):
        text = "Frodo carried the ring to Mordor."
        extractor = make_extractor(json_response())
        extractor.extract(text)

        (call,) = requests_made(extractor)
        (system_block,) = call["system"]
        self.assertIn(
            "Extract relations between people and places.", system_block["text"]
        )
        self.assertEqual({"type": "ephemeral"}, system_block["cache_control"])
        self.assertEqual(text, call["messages"][0]["content"])

    def test_requests_a_json_schema_at_the_configured_effort(self):
        extractor = make_extractor(json_response(), effort="high")
        extractor.extract("Frodo carried the ring to Mordor.")

        (call,) = requests_made(extractor)
        self.assertEqual("claude-opus-5", call["model"])
        self.assertEqual("high", call["output_config"]["effort"])
        self.assertEqual("json_schema", call["output_config"]["format"]["type"])

    def test_rejects_empty_instructions(self):
        with self.assertRaises(ValueError):
            LlmTripletExtractor("   ")


class TestBatchExtract(unittest.TestCase):
    def test_preserves_input_order(self):
        texts = [
            "Frodo carried the ring to Mordor.",
            "Sam cooked potatoes in Ithilien.",
            "Gollum followed the hobbits to Mordor.",
        ]
        extractor = make_extractor(
            *[
                json_response(triplet_dict(*parts, text))
                for text, parts in zip(
                    texts,
                    [
                        ("Frodo", "carried", "the ring"),
                        ("Sam", "cooked", "potatoes"),
                        ("Gollum", "followed", "the hobbits"),
                    ],
                )
            ],
            max_concurrent_requests=1,
        )

        results = list(extractor.batch_extract(iter(texts)))

        self.assertEqual(
            ["Frodo", "Sam", "Gollum"], [ts[0].subj.text for ts in results]
        )

    def test_consumes_input_lazily(self):
        consumed = []

        def texts():
            for text in ["Frodo carried the ring.", "Sam cooked potatoes."]:
                consumed.append(text)
                yield text

        extractor = make_extractor(
            json_response(), json_response(), max_concurrent_requests=1
        )
        batches = extractor.batch_extract(texts())

        next(batches)
        self.assertEqual(1, len(consumed))
        next(batches)
        self.assertEqual(2, len(consumed))


class TestBatchExtractUnordered(unittest.TestCase):
    def test_yields_each_document_as_it_comes_back(self):
        texts = [
            "Frodo carried the ring.",
            "Sam cooked potatoes.",
            "Gollum followed Frodo.",
        ]
        subjects = ["Frodo", "Sam", "Gollum"]
        predicates = ["carried", "cooked", "followed"]
        objects = ["the ring", "potatoes", "Frodo"]
        client = GatedClient(
            {
                text: json_response(triplet_dict(subj, pred, obj, text))
                for text, subj, pred, obj in zip(texts, subjects, predicates, objects)
            }
        )
        extractor = LlmTripletExtractor(
            "Extract relations.", client=client, max_concurrent_requests=3
        )

        results = extractor.batch_extract_unordered(texts)

        # Release the last document first: it should not wait for the first.
        for released in (2, 1, 0):
            client.release(texts[released])
            index, triplets = next(results)
            self.assertEqual(released, index)
            self.assertEqual(subjects[released], triplets[0].subj.text)

    def test_index_identifies_the_source_document(self):
        texts = ["Frodo carried the ring.", "Sam cooked potatoes."]
        extractor = make_extractor(
            json_response(triplet_dict("Frodo", "carried", "the ring", texts[0])),
            json_response(triplet_dict("Sam", "cooked", "potatoes", texts[1])),
            max_concurrent_requests=1,
        )

        results = dict(extractor.batch_extract_unordered(texts))

        self.assertEqual("Frodo", results[0][0].subj.text)
        self.assertEqual("Sam", results[1][0].subj.text)

    def test_consumes_input_lazily(self):
        consumed = []

        def texts():
            for text in ["Frodo carried the ring.", "Sam cooked potatoes."]:
                consumed.append(text)
                yield text

        extractor = make_extractor(
            json_response(), json_response(), max_concurrent_requests=1
        )
        results = extractor.batch_extract_unordered(texts())

        next(results)
        self.assertEqual(1, len(consumed))
        next(results)
        self.assertEqual(2, len(consumed))

    def test_default_implementation_is_ordered(self):
        """Extractors that do not override it keep working, in order."""
        from tests.mocks import MockTripletExtractor

        texts = ["Alice met Bob.", "Carol visited Dave."]

        results = list(MockTripletExtractor().batch_extract_unordered(texts))

        self.assertEqual([0, 1], [index for index, _ in results])
        self.assertEqual("Alice", results[0][1][0].subj.text)
        self.assertEqual("Carol", results[1][1][0].subj.text)


if __name__ == "__main__":
    unittest.main()
