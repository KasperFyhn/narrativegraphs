import unittest

import spacy
from spacy.tokens import Doc

from narrativegraphs.nlp.coref.common import CoreferenceResolver
from narrativegraphs.nlp.coref.fastcoref import FastCorefResolver
from narrativegraphs.nlp.entities.spacy import SpacyEntityExtractor
from narrativegraphs.nlp.triplets.spacy.dependencygraph import DependencyGraphExtractor


class MockCorefResolver(CoreferenceResolver):
    """Lightweight mock resolver for tests — no model required."""

    def __init__(self, mapping: dict[tuple[int, int], tuple[str, int, int]]):
        self._mapping = mapping

    def resolve_doc(self, doc: Doc) -> dict[tuple[int, int], tuple[str, int, int]]:
        return self._mapping


# -----------------------------------------------------------------------
# Entity extractor tests
# -----------------------------------------------------------------------


class TestCorefEntityExtractor(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base_extractor = SpacyEntityExtractor(noun_chunks=True)

    def _make_extractor(self, mapping, remove_pronouns=True):
        return SpacyEntityExtractor(
            noun_chunks=True,
            remove_pronouns=remove_pronouns,
            coref_resolver=MockCorefResolver(mapping),
        )

    def test_resolved_pronoun_emitted_with_antecedent_text(self):
        """Pronoun with a coref mapping → emitted with resolved text, original
        positions."""
        # "Frodo left. He visited Paris." — "Frodo" at 0:5, "He" at 12:14
        text = "Frodo left. He visited Paris."
        he_start, he_end = 12, 14
        frodo_start, frodo_end = 0, 5
        extractor = self._make_extractor(
            {(he_start, he_end): ("Frodo", frodo_start, frodo_end)}
        )
        entities = extractor.extract(text)

        texts = [e.text for e in entities]
        self.assertIn("Frodo", texts)
        self.assertIn("Paris", texts)

        resolved = next(
            e for e in entities if e.text == "Frodo" and e.start_char == he_start
        )
        self.assertEqual(resolved.start_char, he_start)
        self.assertEqual(resolved.end_char, he_end)

    def test_unresolved_pronoun_filtered_when_remove_pronouns_true(self):
        """Pronoun with no coref mapping + remove_pronouns=True → filtered out."""
        text = "He visited Paris."
        extractor = self._make_extractor({}, remove_pronouns=True)
        entities = extractor.extract(text)

        texts = [e.text for e in entities]
        self.assertNotIn("He", texts)
        self.assertIn("Paris", texts)

    def test_unresolved_pronoun_kept_when_remove_pronouns_false(self):
        """Pronoun with no coref mapping + remove_pronouns=False → kept as-is."""
        text = "He visited Paris."
        extractor = self._make_extractor({}, remove_pronouns=False)
        entities = extractor.extract(text)

        texts = [e.text for e in entities]
        self.assertIn("He", texts)

    def test_non_pronoun_entities_unaffected(self):
        """Non-pronoun entities pass through regardless of coref resolver."""
        text = "Alice visited Paris."
        extractor = self._make_extractor({})
        entities = extractor.extract(text)

        texts = [e.text for e in entities]
        self.assertIn("Alice", texts)
        self.assertIn("Paris", texts)

    def test_no_resolver_behavior_unchanged(self):
        """Without a coref resolver, remove_pronouns=True still filters pronouns."""
        text = "He visited Paris."
        entities = self.base_extractor.extract(text)

        texts = [e.text for e in entities]
        self.assertNotIn("He", texts)
        self.assertIn("Paris", texts)


# -----------------------------------------------------------------------
# Triplet extractor tests
# -----------------------------------------------------------------------


class TestCorefTripletExtractor(unittest.TestCase):
    def _make_extractor(self, mapping, remove_pronoun_entities=True):
        return DependencyGraphExtractor(
            noun_chunks=True,
            remove_pronoun_entities=remove_pronoun_entities,
            coref_resolver=MockCorefResolver(mapping),
        )

    def test_resolved_pronoun_subject_appears_in_triplet(self):
        """Pronoun subject resolved via coref → triplet subject has resolved text."""
        # "Frodo left. He visited Paris." — "Frodo" at 0:5, "He" at 12:14
        text = "Frodo left. He visited Paris."
        he_start, he_end = 12, 14
        frodo_start, frodo_end = 0, 5
        extractor = self._make_extractor(
            {(he_start, he_end): ("Frodo", frodo_start, frodo_end)}
        )
        triplets = extractor.extract(text)

        self.assertTrue(len(triplets) > 0, "Expected at least one triplet")
        subj_texts = [t.subj.text for t in triplets]
        self.assertIn("Frodo", subj_texts)

        resolved_triplet = next(t for t in triplets if t.subj.text == "Frodo")
        self.assertEqual(resolved_triplet.subj.start_char, he_start)
        self.assertEqual(resolved_triplet.subj.end_char, he_end)

    def test_unresolved_pronoun_filtered_from_triplets(self):
        """Unresolved pronoun subject with remove_pronoun_entities=True → no triplet."""
        text = "He visited Paris."
        extractor = self._make_extractor({}, remove_pronoun_entities=True)
        triplets = extractor.extract(text)

        subj_texts = [t.subj.text for t in triplets]
        self.assertNotIn("He", subj_texts)

    def test_no_resolver_behavior_unchanged(self):
        """Without resolver, pronoun filtering behaves as before."""
        extractor = DependencyGraphExtractor(
            noun_chunks=True, remove_pronoun_entities=True
        )
        text = "He visited Paris."
        triplets = extractor.extract(text)

        subj_texts = [t.subj.text for t in triplets]
        self.assertNotIn("He", subj_texts)


# -----------------------------------------------------------------------
# FastCorefResolver.resolve_doc logic (no fastcoref install required)
# -----------------------------------------------------------------------


class _TestableFastCorefResolver(FastCorefResolver):
    """Bypasses the fastcoref import in __init__ so resolve_doc can be unit-tested."""

    def __init__(self):
        self._model = "FCoref"  # skip import check


class TestFastCorefResolverLogic(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.nlp = spacy.load("en_core_web_sm")
        if not Doc.has_extension("coref_clusters"):
            Doc.set_extension("coref_clusters", default=[])
        cls.resolver = _TestableFastCorefResolver()

    def _doc(self, text, clusters):
        doc = self.nlp(text)
        doc._.coref_clusters = clusters
        return doc

    def test_cataphora_pronoun_resolves_to_later_named_mention(self):
        """Pronoun before its referent → named entity chosen as antecedent."""
        # "Before he left, Frodo said goodbye."
        #          ^7:9           ^16:21
        text = "Before he left, Frodo said goodbye."
        he = (7, 9)
        frodo = (16, 21)
        doc = self._doc(text, [[he, frodo]])
        coref_map = self.resolver.resolve_doc(doc)

        self.assertIn(he, coref_map)
        ant_text, _, _ = coref_map[he]
        self.assertEqual(ant_text, "Frodo")
        self.assertNotIn(frodo, coref_map)

    def test_all_pronouns_cluster_produces_no_mappings(self):
        """Cluster where every mention is a pronoun → skipped entirely."""
        # "He told him that he was wrong."
        #   ^0:2    ^8:11       ^17:19
        text = "He told him that he was wrong."
        doc = self._doc(text, [[(0, 2), (8, 11), (17, 19)]])
        coref_map = self.resolver.resolve_doc(doc)

        self.assertEqual(coref_map, {})


if __name__ == "__main__":
    unittest.main()
