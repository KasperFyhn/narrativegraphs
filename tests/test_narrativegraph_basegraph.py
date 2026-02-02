"""Tests for NarrativeGraph backwards compatibility after BaseGraph refactoring."""

import unittest

from narrativegraphs import NarrativeGraph
from narrativegraphs.basegraph import BaseGraph
from tests.mocks import MockMapper, MockTripletExtractor


class TestNarrativeGraphInheritance(unittest.TestCase):
    def test_narrativegraph_inherits_from_basegraph(self):
        """Test that NarrativeGraph inherits from BaseGraph."""
        self.assertTrue(issubclass(NarrativeGraph, BaseGraph))

    def test_cooccurrence_only_flag_is_false(self):
        """Test that NarrativeGraph._cooccurrence_only is False."""
        ng = NarrativeGraph()
        self.assertFalse(ng._cooccurrence_only)


class TestNarrativeGraphBackwardsCompatibility(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Create a NarrativeGraph for testing."""
        cls.ng = NarrativeGraph(
            triplet_extractor=MockTripletExtractor(),
            entity_mapper=MockMapper(),
            predicate_mapper=MockMapper(),
        )
        cls.ng.fit(["Alice met Bob.", "Carol visited Dave."])

    def test_has_entities_property(self):
        """Test that NarrativeGraph still has entities_ property."""
        entities = self.ng.entities_
        self.assertIsNotNone(entities)
        self.assertGreater(len(entities), 0)

    def test_has_predicates_property(self):
        """Test that NarrativeGraph still has predicates_ property."""
        predicates = self.ng.predicates_
        self.assertIsNotNone(predicates)
        self.assertGreater(len(predicates), 0)

    def test_has_relations_property(self):
        """Test that NarrativeGraph still has relations_ property."""
        relations = self.ng.relations_
        self.assertIsNotNone(relations)
        self.assertGreater(len(relations), 0)

    def test_has_cooccurrences_property(self):
        """Test that NarrativeGraph still has cooccurrences_ property."""
        cooccurrences = self.ng.cooccurrences_
        self.assertIsNotNone(cooccurrences)
        self.assertGreater(len(cooccurrences), 0)

    def test_has_documents_property(self):
        """Test that NarrativeGraph still has documents_ property."""
        documents = self.ng.documents_
        self.assertIsNotNone(documents)
        self.assertEqual(len(documents), 2)

    def test_has_triplets_property(self):
        """Test that NarrativeGraph still has triplets_ property."""
        triplets = self.ng.triplets_
        self.assertIsNotNone(triplets)
        self.assertGreater(len(triplets), 0)

    def test_has_relation_graph_property(self):
        """Test that NarrativeGraph still has relation_graph_ property."""
        graph = self.ng.relation_graph_
        self.assertIsNotNone(graph)
        self.assertGreater(len(graph.nodes), 0)

    def test_has_cooccurrence_graph_property(self):
        """Test that NarrativeGraph still has cooccurrence_graph_ property."""
        graph = self.ng.cooccurrence_graph_
        self.assertIsNotNone(graph)
        self.assertGreater(len(graph.nodes), 0)

    def test_fit_returns_self(self):
        """Test that fit() returns self for method chaining."""
        ng = NarrativeGraph(
            triplet_extractor=MockTripletExtractor(),
            entity_mapper=MockMapper(),
            predicate_mapper=MockMapper(),
        )
        result = ng.fit(["Alice met Bob."])
        self.assertIs(result, ng)


class TestBaseGraphSharedMethods(unittest.TestCase):
    """Test that BaseGraph shared methods work correctly in NarrativeGraph."""

    def test_has_serve_visualizer_method(self):
        """Test that NarrativeGraph has serve_visualizer method."""
        ng = NarrativeGraph()
        self.assertTrue(hasattr(ng, "serve_visualizer"))
        self.assertTrue(callable(ng.serve_visualizer))

    def test_has_save_to_file_method(self):
        """Test that NarrativeGraph has save_to_file method."""
        ng = NarrativeGraph()
        self.assertTrue(hasattr(ng, "save_to_file"))
        self.assertTrue(callable(ng.save_to_file))

    def test_has_load_classmethod(self):
        """Test that NarrativeGraph has load classmethod."""
        self.assertTrue(hasattr(NarrativeGraph, "load"))
        self.assertTrue(callable(NarrativeGraph.load))


if __name__ == "__main__":
    unittest.main()
