"""Tests for CooccurrenceGraph-specific functionality.

Shared functionality (persistence, base properties) is tested in test_basegraph.py.
"""

import unittest
from datetime import date

from narrativegraphs import CooccurrenceGraph
from narrativegraphs.nlp.entities.spacy import SpacyEntityExtractor
from tests.mocks import MockEntityExtractor, MockMapper


class TestCooccurrenceGraphSpecific(unittest.TestCase):
    def test_cooccurrence_only_flag_is_true(self):
        """CooccurrenceGraph has _cooccurrence_only=True."""
        cg = CooccurrenceGraph()
        self.assertTrue(cg._cooccurrence_only)

    def test_fit_returns_self(self):
        """fit() returns self for method chaining."""
        cg = CooccurrenceGraph(
            entity_extractor=MockEntityExtractor(),
            entity_mapper=MockMapper(),
        )
        result = cg.fit(["Alice met Bob."])
        self.assertIs(result, cg)

    def test_lacks_narrativegraph_properties(self):
        """CooccurrenceGraph does not have NarrativeGraph-specific properties."""
        cg = CooccurrenceGraph(
            entity_extractor=MockEntityExtractor(),
            entity_mapper=MockMapper(),
        )
        cg.fit(["Alice met Bob."])

        # These properties are only on NarrativeGraph
        self.assertFalse(hasattr(cg, "predicates_"))
        self.assertFalse(hasattr(cg, "relations_"))
        self.assertFalse(hasattr(cg, "triplets_"))
        self.assertFalse(hasattr(cg, "relation_graph_"))


class TestCooccurrenceGraphFitParameters(unittest.TestCase):
    def test_fit_with_doc_ids(self):
        """fit() accepts document IDs."""
        cg = CooccurrenceGraph(
            entity_extractor=MockEntityExtractor(),
            entity_mapper=MockMapper(),
        )
        cg.fit(["Doc one.", "Doc two."], doc_ids=["id1", "id2"])
        self.assertEqual(len(cg.documents_), 2)

    def test_fit_with_timestamps(self):
        """fit() accepts timestamps."""
        cg = CooccurrenceGraph(
            entity_extractor=MockEntityExtractor(),
            entity_mapper=MockMapper(),
        )
        cg.fit(
            ["Doc one.", "Doc two."],
            timestamps=[date(2024, 1, 1), date(2024, 1, 2)],
        )
        self.assertEqual(len(cg.documents_), 2)

    def test_fit_with_categories(self):
        """fit() accepts categories."""
        cg = CooccurrenceGraph(
            entity_extractor=MockEntityExtractor(),
            entity_mapper=MockMapper(),
        )
        cg.fit(["Doc one.", "Doc two."], categories=["cat1", "cat2"])
        self.assertEqual(len(cg.documents_), 2)


class TestCooccurrenceGraphIntegration(unittest.TestCase):
    def test_with_spacy_extractor(self):
        """Integration test with real SpacyEntityExtractor."""
        cg = CooccurrenceGraph(
            entity_extractor=SpacyEntityExtractor(),
            entity_mapper=MockMapper(),
            n_cpu=1,
        )
        cg.fit(["Alice met Bob in Paris.", "Bob visited Paris with Carol."])

        self.assertGreater(len(cg.entities_), 0)
        self.assertGreater(len(cg.cooccurrences_), 0)
        self.assertEqual(len(cg.documents_), 2)
        self.assertGreater(len(cg.cooccurrence_graph_.nodes), 0)


if __name__ == "__main__":
    unittest.main()
