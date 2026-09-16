"""Pipelines loaded from the same model share one vocabulary but stay separate.

spaCy does not cache loaded models, because a Language object is mutable and
this package reconfigures it in conflicting ways: the triplet extractor needs
the parser enabled, the mapping normalizer disables it. Sharing the Vocab gets
the memory saving without that hazard.
"""

import unittest

import spacy

import narrativegraphs.nlp.common.spacy as spacy_utils
from narrativegraphs.nlp.common.spacy import (
    build_spacy_pipeline,
    clear_shared_vocabs,
    ensure_spacy_model,
)

MODEL = "en_core_web_sm"

TEXTS = [
    "Frodo carried the ring to Mordor, and Sam followed him closely.",
    "The Ministry of Foreign Affairs announced that Denmark would not sign.",
    "She hasn't been running the lab since 2019; her students took over.",
]


def analyse(nlp):
    """Everything downstream code reads off a parsed document."""
    analysis = []
    for doc in nlp.pipe(TEXTS):
        analysis.append(
            [
                (t.text, t.lemma_, t.pos_, t.tag_, t.dep_, t.head.i, t.ent_type_)
                for t in doc
            ]
        )
        analysis.append([(e.text, e.label_) for e in doc.ents])
        analysis.append([s.text for s in doc.sents])
    return analysis


class TestSharedVocab(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.baseline = analyse(spacy.load(MODEL))

    def setUp(self):
        clear_shared_vocabs()

    def tearDown(self):
        clear_shared_vocabs()

    def test_vocab_is_reused_across_loads(self):
        first = ensure_spacy_model(MODEL)
        second = ensure_spacy_model(MODEL)

        self.assertIs(first.vocab, second.vocab)

    def test_each_load_is_its_own_pipeline(self):
        first = ensure_spacy_model(MODEL)
        second = ensure_spacy_model(MODEL)

        self.assertIsNot(first, second)

    def test_reconfiguring_one_leaves_the_others_alone(self):
        extractor_nlp = ensure_spacy_model(MODEL)
        mapper_nlp = ensure_spacy_model(MODEL)

        # What spacy_normalizer does, and what makes caching Language unsafe.
        mapper_nlp.disable_pipe("parser")

        self.assertIn("parser", mapper_nlp.disabled)
        self.assertNotIn("parser", extractor_nlp.disabled)

    def test_added_components_do_not_leak(self):
        extractor_nlp = build_spacy_pipeline(MODEL, True, None)
        mapper_nlp = ensure_spacy_model(MODEL)

        self.assertIn("custom_sentencizer", extractor_nlp.pipe_names)
        self.assertNotIn("custom_sentencizer", mapper_nlp.pipe_names)

    def test_sharing_a_vocab_does_not_change_the_analysis(self):
        created_vocab = ensure_spacy_model(MODEL)
        shared_vocab = ensure_spacy_model(MODEL)

        self.assertEqual(self.baseline, analyse(created_vocab))
        self.assertEqual(self.baseline, analyse(shared_vocab))

    def test_analysis_survives_another_pipeline_being_reconfigured(self):
        extractor_nlp = ensure_spacy_model(MODEL)
        ensure_spacy_model(MODEL).disable_pipe("parser")

        self.assertEqual(self.baseline, analyse(extractor_nlp))

    def test_enable_limits_the_pipeline_without_a_separate_vocab(self):
        full = ensure_spacy_model(MODEL)
        tokenizer_only = ensure_spacy_model(MODEL, enable=["tokenizer"])

        self.assertIs(full.vocab, tokenizer_only.vocab)
        self.assertEqual([], list(tokenizer_only.pipe_names))

    def test_clearing_drops_the_shared_vocab(self):
        first = ensure_spacy_model(MODEL)
        clear_shared_vocabs()
        second = ensure_spacy_model(MODEL)

        self.assertIsNot(first.vocab, second.vocab)

    def test_vocabs_are_kept_per_model_name(self):
        """A different model must never be handed another model's vocab."""
        ensure_spacy_model(MODEL)

        self.assertEqual([MODEL], list(spacy_utils._shared_vocabs))


if __name__ == "__main__":
    unittest.main()
