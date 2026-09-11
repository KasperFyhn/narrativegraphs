"""Tests for NarrativeGraph-specific functionality.

Shared functionality (persistence, base properties) is tested in test_basegraph.py.
"""

import tempfile
import unittest

import networkx as nx
import pandas as pd

from narrativegraphs import NarrativeGraph
from tests.mocks import MockMapper, MockTripletExtractor


class TestNarrativeGraphSpecific(unittest.TestCase):
    def test_fit_returns_self(self):
        """fit() returns self for method chaining."""
        ng = NarrativeGraph(
            triplet_extractor=MockTripletExtractor(),
            entity_mapper=MockMapper(),
            predicate_mapper=MockMapper(),
        )
        result = ng.fit(["Alice met Bob."])
        self.assertIs(result, ng)

    def test_load_returns_narrativegraph(self):
        with tempfile.NamedTemporaryFile(suffix=".db") as f:
            ng = NarrativeGraph()
            ng.save_to_file(f.name, overwrite=True)
            loaded = NarrativeGraph.load(f.name)
            self.assertIsInstance(loaded, NarrativeGraph)


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


class TestFitWithPrecomputedTriplets(unittest.TestCase):
    """Extraction done elsewhere — a batch run collected later, or reused."""

    docs = ["Alice met Bob.", "Carol visited Dave."]

    def triplets(self):
        return [MockTripletExtractor().extract(doc) for doc in self.docs]

    def graph(self, **kwargs):
        return NarrativeGraph(
            entity_mapper=MockMapper(), predicate_mapper=MockMapper(), **kwargs
        )

    def test_extractor_is_not_run(self):
        class ExplodingExtractor(MockTripletExtractor):
            def extract(self, text):
                raise AssertionError("the extractor should not have run")

            def batch_extract(self, texts, n_cpu=1, **kwargs):
                raise AssertionError("the extractor should not have run")

            def batch_extract_unordered(self, texts, n_cpu=1, **kwargs):
                raise AssertionError("the extractor should not have run")

        ng = self.graph(triplet_extractor=ExplodingExtractor()).fit(
            self.docs, triplets=self.triplets()
        )

        self.assertGreater(len(ng.relations_), 0)

    def test_gives_the_same_graph_as_extracting_inline(self):
        extracted = self.graph(triplet_extractor=MockTripletExtractor()).fit(self.docs)
        precomputed = self.graph(triplet_extractor=MockTripletExtractor()).fit(
            self.docs, triplets=self.triplets()
        )

        self.assertEqual(
            sorted(extracted.entities_["label"]),
            sorted(precomputed.entities_["label"]),
        )
        self.assertEqual(len(extracted.relations_), len(precomputed.relations_))

    def test_rejects_a_mismatched_number_of_lists(self):
        graph = self.graph(triplet_extractor=MockTripletExtractor())

        with self.assertRaises(ValueError):
            graph.fit(self.docs, triplets=[[]])

    def test_documents_are_still_stored(self):
        ng = self.graph(triplet_extractor=MockTripletExtractor()).fit(
            self.docs, triplets=self.triplets()
        )

        self.assertEqual(len(self.docs), len(ng.documents_))


class TestAllEntityOccurrences(unittest.TestCase):
    """Every mention is recorded, not only those taking part in a relation."""

    docs = ["Frodo carried the ring. Later Frodo rested. Then Frodo slept."]

    def setUp(self):
        self.ng = NarrativeGraph(
            triplet_extractor=MockTripletExtractor(),
            entity_mapper=MockMapper(),
            predicate_mapper=MockMapper(),
        ).fit(self.docs)

    def test_records_repeated_mentions(self):
        mentions = self.ng.entity_mentions_
        frodo = mentions[mentions["entity_span_text"] == "Frodo"]

        # The extractor reports one relation; the document says "Frodo" thrice.
        self.assertEqual(3, len(frodo))

    def test_triplets_still_resolve_to_their_own_occurrences(self):
        """Population looks triplets up by exact span; expansion must not break it."""
        self.assertGreater(len(self.ng.relations_), 0)

    def test_mentions_do_not_overlap(self):
        mentions = self.ng.entity_mentions_
        spans = sorted(zip(mentions["entity_span_start"], mentions["entity_span_end"]))

        for current, following in zip(spans, spans[1:]):
            self.assertLessEqual(current[1], following[0])


if __name__ == "__main__":
    unittest.main()
