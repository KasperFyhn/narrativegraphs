"""Tests for NarrativeGraph-specific functionality.

Shared functionality (persistence, base properties) is tested in test_basegraph.py.
"""

import unittest

import networkx as nx
import pandas as pd

from narrativegraphs import NarrativeGraph
from tests.mocks import MockMapper, MockTripletExtractor


class TestNarrativeGraphSpecific(unittest.TestCase):
    def test_cooccurrence_only_flag_is_false(self):
        """NarrativeGraph has _cooccurrence_only=False."""
        ng = NarrativeGraph()
        self.assertFalse(ng._cooccurrence_only)

    def test_fit_returns_self(self):
        """fit() returns self for method chaining."""
        ng = NarrativeGraph(
            triplet_extractor=MockTripletExtractor(),
            entity_mapper=MockMapper(),
            predicate_mapper=MockMapper(),
        )
        result = ng.fit(["Alice met Bob."])
        self.assertIs(result, ng)


class TestNarrativeGraphProperties(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ng = NarrativeGraph(
            triplet_extractor=MockTripletExtractor(),
            entity_mapper=MockMapper(),
            predicate_mapper=MockMapper(),
        )
        cls.ng.fit(["Alice met Bob.", "Carol visited Dave."])

    def test_predicates_returns_dataframe(self):
        """predicates_ returns a pandas DataFrame."""
        predicates = self.ng.predicates_
        self.assertIsInstance(predicates, pd.DataFrame)
        self.assertGreater(len(predicates), 0)

    def test_relations_returns_dataframe(self):
        """relations_ returns a pandas DataFrame."""
        relations = self.ng.relations_
        self.assertIsInstance(relations, pd.DataFrame)
        self.assertGreater(len(relations), 0)

    def test_triplets_returns_dataframe(self):
        """triplets_ returns a pandas DataFrame."""
        triplets = self.ng.triplets_
        self.assertIsInstance(triplets, pd.DataFrame)
        self.assertGreater(len(triplets), 0)

    def test_relation_graph_returns_digraph(self):
        """relation_graph_ returns a NetworkX DiGraph."""
        graph = self.ng.relation_graph_
        self.assertIsInstance(graph, nx.DiGraph)
        self.assertGreater(len(graph.nodes), 0)

    def test_also_has_cooccurrence_graph(self):
        """NarrativeGraph also has cooccurrence_graph_ (inherited)."""
        graph = self.ng.cooccurrence_graph_
        self.assertIsInstance(graph, nx.Graph)
        self.assertGreater(len(graph.nodes), 0)


if __name__ == "__main__":
    unittest.main()
