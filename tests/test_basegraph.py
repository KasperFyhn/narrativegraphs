"""Tests for BaseGraph shared functionality.

Tests persistence, properties, and behaviors shared by CooccurrenceGraph
and NarrativeGraph. Uses CooccurrenceGraph as the concrete implementation.
"""

import os
import tempfile
import unittest

import networkx as nx
import pandas as pd

from narrativegraphs import CooccurrenceGraph
from tests.mocks import MockEntityExtractor, MockMapper


class TestBaseGraphInit(unittest.TestCase):
    def test_default_creates_memory_db(self):
        """Default initialization creates an in-memory database."""
        cg = CooccurrenceGraph()
        self.assertEqual(str(cg._engine.url), "sqlite:///:memory:")

    def test_file_db_creation(self):
        """Initialization with sqlite_db_path creates file database."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=True) as tmp:
            cg = CooccurrenceGraph(sqlite_db_path=tmp.name)
            self.assertIn(tmp.name, str(cg._engine.url))

    def test_on_existing_db_stop_raises_when_data_exists(self):
        """on_existing_db='stop' raises error if database has data."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
            tmp_path = tmp.name
        try:
            cg1 = CooccurrenceGraph(
                sqlite_db_path=tmp_path,
                entity_extractor=MockEntityExtractor(),
                entity_mapper=MockMapper(),
            )
            cg1.fit(["Test document."])

            with self.assertRaises(FileExistsError):
                CooccurrenceGraph(sqlite_db_path=tmp_path, on_existing_db="stop")
        finally:
            os.unlink(tmp_path)

    def test_on_existing_db_overwrite_clears_data(self):
        """on_existing_db='overwrite' removes existing database."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
            tmp_path = tmp.name
        try:
            cg1 = CooccurrenceGraph(
                sqlite_db_path=tmp_path,
                entity_extractor=MockEntityExtractor(),
                entity_mapper=MockMapper(),
            )
            cg1.fit(["Test document."])

            cg2 = CooccurrenceGraph(
                sqlite_db_path=tmp_path,
                on_existing_db="overwrite",
                entity_extractor=MockEntityExtractor(),
                entity_mapper=MockMapper(),
            )
            self.assertEqual(len(cg2.documents_), 0)
        finally:
            os.unlink(tmp_path)

    def test_on_existing_db_reuse_keeps_data(self):
        """on_existing_db='reuse' preserves existing database data."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
            tmp_path = tmp.name
        try:
            cg1 = CooccurrenceGraph(
                sqlite_db_path=tmp_path,
                entity_extractor=MockEntityExtractor(),
                entity_mapper=MockMapper(),
            )
            cg1.fit(["Test document."])
            original_count = len(cg1.documents_)

            cg2 = CooccurrenceGraph(sqlite_db_path=tmp_path, on_existing_db="reuse")
            self.assertEqual(len(cg2.documents_), original_count)
        finally:
            os.unlink(tmp_path)


class TestBaseGraphProperties(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.graph = CooccurrenceGraph(
            entity_extractor=MockEntityExtractor(),
            entity_mapper=MockMapper(),
        )
        cls.graph.fit(["Alice met Bob.", "Carol visited Dave."])

    def test_entities_returns_dataframe(self):
        """entities_ returns a pandas DataFrame with entity data."""
        entities = self.graph.entities_
        self.assertIsInstance(entities, pd.DataFrame)
        self.assertGreater(len(entities), 0)
        self.assertIn("label", entities.columns)

    def test_cooccurrences_returns_dataframe(self):
        """cooccurrences_ returns a pandas DataFrame with cooccurrence data."""
        cooccurrences = self.graph.cooccurrences_
        self.assertIsInstance(cooccurrences, pd.DataFrame)
        self.assertGreater(len(cooccurrences), 0)

    def test_documents_returns_dataframe(self):
        """documents_ returns a pandas DataFrame with document data."""
        documents = self.graph.documents_
        self.assertIsInstance(documents, pd.DataFrame)
        self.assertEqual(len(documents), 2)

    def test_cooccurrence_graph_returns_networkx_graph(self):
        """cooccurrence_graph_ returns a NetworkX Graph."""
        graph = self.graph.cooccurrence_graph_
        self.assertIsInstance(graph, nx.Graph)
        self.assertGreater(len(graph.nodes), 0)


class TestBaseGraphPersistence(unittest.TestCase):
    def test_save_to_file_no_overwrite_raises(self):
        """save_to_file with overwrite=False raises if file exists."""
        cg = CooccurrenceGraph(
            entity_extractor=MockEntityExtractor(),
            entity_mapper=MockMapper(),
        )
        cg.fit(["Test."])

        with tempfile.NamedTemporaryFile(suffix=".db") as tmp:
            with self.assertRaises(FileExistsError):
                cg.save_to_file(tmp.name, overwrite=False)

    def test_save_and_load_preserves_data(self):
        """Saving and loading preserves all data."""
        cg1 = CooccurrenceGraph(
            entity_extractor=MockEntityExtractor(),
            entity_mapper=MockMapper(),
        )
        cg1.fit(["Alice met Bob.", "Carol visited Dave."])

        with tempfile.NamedTemporaryFile(suffix=".db", delete=True) as tmp:
            cg1.save_to_file(tmp.name, overwrite=True)
            cg2 = CooccurrenceGraph.load(tmp.name)

            self.assertEqual(len(cg1.documents_), len(cg2.documents_))
            self.assertEqual(len(cg1.entities_), len(cg2.entities_))
            self.assertEqual(len(cg1.cooccurrences_), len(cg2.cooccurrences_))

    def test_load_nonexistent_file_raises(self):
        """Loading a non-existent file raises FileNotFoundError."""
        with self.assertRaises(FileNotFoundError):
            CooccurrenceGraph.load("nonexistent_file.db")

    def test_save_adds_db_extension(self):
        """save_to_file adds .db extension if missing."""
        cg = CooccurrenceGraph(
            entity_extractor=MockEntityExtractor(),
            entity_mapper=MockMapper(),
        )
        cg.fit(["Test."])

        with tempfile.TemporaryDirectory() as tmpdir:
            path = f"{tmpdir}/test"
            cg.save_to_file(path)
            loaded = CooccurrenceGraph.load(path)
            self.assertEqual(len(loaded.documents_), 1)


if __name__ == "__main__":
    unittest.main()
