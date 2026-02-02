import tempfile
import unittest

from narrativegraphs import CooccurrenceGraph
from narrativegraphs.nlp.extraction import EntityExtractor, SpacyEntityExtractor
from narrativegraphs.nlp.extraction.common import SpanAnnotation
from narrativegraphs.nlp.mapping import Mapper


class MockEntityExtractor(EntityExtractor):
    """Mock entity extractor for fast testing."""

    def extract(self, text: str) -> list[SpanAnnotation]:
        # Simple extraction: split by spaces, take capitalized words as entities
        entities = []
        pos = 0
        for word in text.split():
            start = text.find(word, pos)
            end = start + len(word)
            # Remove punctuation for checking
            clean_word = word.strip(".,!?;:")
            if clean_word and clean_word[0].isupper():
                entities.append(
                    SpanAnnotation(
                        text=clean_word,
                        start_char=start,
                        end_char=start + len(clean_word),
                    )
                )
            pos = end
        return entities


class MockMapper(Mapper):
    """Mock mapper that returns identity mapping."""

    def create_mapping(self, labels: list[str]) -> dict[str, str]:
        return {label: label for label in labels}


class TestCooccurrenceGraph(unittest.TestCase):
    def test_init_creates_memory_db(self):
        """Test default initialization creates in-memory database."""
        cg = CooccurrenceGraph()
        self.assertEqual(str(cg._engine.url), "sqlite:///:memory:")

    def test_fit_extracts_entities(self):
        """Test that fit() extracts entities from documents."""
        cg = CooccurrenceGraph(
            entity_extractor=MockEntityExtractor(),
            entity_mapper=MockMapper(),
        )
        cg.fit(["Alice met Bob.", "Carol visited Dave."])

        entities = cg.entities_
        self.assertGreater(len(entities), 0)

        entity_labels = set(entities["label"].tolist())
        self.assertIn("Alice", entity_labels)
        self.assertIn("Bob", entity_labels)
        self.assertIn("Carol", entity_labels)
        self.assertIn("Dave", entity_labels)

    def test_fit_creates_cooccurrences(self):
        """Test that fit() creates cooccurrence relationships."""
        cg = CooccurrenceGraph(
            entity_extractor=MockEntityExtractor(),
            entity_mapper=MockMapper(),
        )
        cg.fit(["Alice met Bob in Paris."])

        cooccurrences = cg.cooccurrences_
        self.assertGreater(len(cooccurrences), 0)

    def test_fit_stores_documents(self):
        """Test that fit() stores documents."""
        cg = CooccurrenceGraph(
            entity_extractor=MockEntityExtractor(),
            entity_mapper=MockMapper(),
        )
        docs = ["Document one.", "Document two.", "Document three."]
        cg.fit(docs)

        documents = cg.documents_
        self.assertEqual(len(documents), 3)

    def test_cooccurrence_graph_property(self):
        """Test that cooccurrence_graph_ returns a NetworkX graph."""
        cg = CooccurrenceGraph(
            entity_extractor=MockEntityExtractor(),
            entity_mapper=MockMapper(),
        )
        cg.fit(["Alice met Bob.", "Bob visited Carol."])

        graph = cg.cooccurrence_graph_
        self.assertIsNotNone(graph)
        self.assertGreater(len(graph.nodes), 0)

    def test_no_relation_graph_property(self):
        """Test that CooccurrenceGraph does not have relation_graph_."""
        cg = CooccurrenceGraph(
            entity_extractor=MockEntityExtractor(),
            entity_mapper=MockMapper(),
        )
        cg.fit(["Alice met Bob."])

        self.assertFalse(hasattr(cg, "relation_graph_"))

    def test_no_predicates_property(self):
        """Test that CooccurrenceGraph does not have predicates_."""
        cg = CooccurrenceGraph(
            entity_extractor=MockEntityExtractor(),
            entity_mapper=MockMapper(),
        )
        cg.fit(["Alice met Bob."])

        self.assertFalse(hasattr(cg, "predicates_"))

    def test_no_relations_property(self):
        """Test that CooccurrenceGraph does not have relations_."""
        cg = CooccurrenceGraph(
            entity_extractor=MockEntityExtractor(),
            entity_mapper=MockMapper(),
        )
        cg.fit(["Alice met Bob."])

        self.assertFalse(hasattr(cg, "relations_"))

    def test_no_triplets_property(self):
        """Test that CooccurrenceGraph does not have triplets_."""
        cg = CooccurrenceGraph(
            entity_extractor=MockEntityExtractor(),
            entity_mapper=MockMapper(),
        )
        cg.fit(["Alice met Bob."])

        self.assertFalse(hasattr(cg, "triplets_"))

    def test_cooccurrence_only_flag(self):
        """Test that _cooccurrence_only is True."""
        cg = CooccurrenceGraph()
        self.assertTrue(cg._cooccurrence_only)

    def test_fit_returns_self(self):
        """Test that fit() returns self for method chaining."""
        cg = CooccurrenceGraph(
            entity_extractor=MockEntityExtractor(),
            entity_mapper=MockMapper(),
        )
        result = cg.fit(["Alice met Bob."])
        self.assertIs(result, cg)

    def test_fit_with_doc_ids(self):
        """Test fit() with document IDs."""
        cg = CooccurrenceGraph(
            entity_extractor=MockEntityExtractor(),
            entity_mapper=MockMapper(),
        )
        cg.fit(
            ["Doc one.", "Doc two."],
            doc_ids=["id1", "id2"],
        )

        documents = cg.documents_
        self.assertEqual(len(documents), 2)

    def test_fit_with_timestamps(self):
        """Test fit() with timestamps."""
        from datetime import date

        cg = CooccurrenceGraph(
            entity_extractor=MockEntityExtractor(),
            entity_mapper=MockMapper(),
        )
        cg.fit(
            ["Doc one.", "Doc two."],
            timestamps=[date(2024, 1, 1), date(2024, 1, 2)],
        )

        documents = cg.documents_
        self.assertEqual(len(documents), 2)

    def test_fit_with_categories(self):
        """Test fit() with categories."""
        cg = CooccurrenceGraph(
            entity_extractor=MockEntityExtractor(),
            entity_mapper=MockMapper(),
        )
        cg.fit(
            ["Doc one.", "Doc two."],
            categories=["cat1", "cat2"],
        )

        documents = cg.documents_
        self.assertEqual(len(documents), 2)

    def test_save_and_load(self):
        """Test saving and loading a CooccurrenceGraph."""
        cg1 = CooccurrenceGraph(
            entity_extractor=MockEntityExtractor(),
            entity_mapper=MockMapper(),
        )
        cg1.fit(["Alice met Bob.", "Carol visited Dave."])

        with tempfile.NamedTemporaryFile(suffix=".db") as tmp:
            cg1.save_to_file(tmp.name)

            cg2 = CooccurrenceGraph.load(tmp.name)

            # Verify data persisted
            self.assertEqual(len(cg1.documents_), len(cg2.documents_))
            self.assertEqual(len(cg1.entities_), len(cg2.entities_))
            self.assertEqual(len(cg1.cooccurrences_), len(cg2.cooccurrences_))

    def test_load_nonexistent_file_raises(self):
        """Test that loading non-existent file raises error."""
        with self.assertRaises(FileNotFoundError):
            CooccurrenceGraph.load("nonexistent.db")

    def test_with_real_extractor(self):
        """Integration test with real SpacyEntityExtractor."""
        cg = CooccurrenceGraph(
            entity_extractor=SpacyEntityExtractor(),
            entity_mapper=MockMapper(),
        )
        cg.fit(["Alice met Bob in Paris.", "Bob visited Paris with Carol."])

        # Should have entities
        entities = cg.entities_
        self.assertGreater(len(entities), 0)

        # Should have cooccurrences
        cooccurrences = cg.cooccurrences_
        self.assertGreater(len(cooccurrences), 0)

        # Should have documents
        documents = cg.documents_
        self.assertEqual(len(documents), 2)

        # Should have cooccurrence graph
        graph = cg.cooccurrence_graph_
        self.assertGreater(len(graph.nodes), 0)


class TestCooccurrenceGraphFileHandling(unittest.TestCase):
    def test_init_file_db_new(self):
        """Test initialization with new file database."""
        with tempfile.NamedTemporaryFile(delete=True) as tmp:
            cg = CooccurrenceGraph(sqlite_db_path=tmp.name)
            self.assertEqual(str(cg._engine.url), "sqlite:///" + tmp.name)

    def test_init_file_db_overwrite(self):
        """Test initialization with overwrite behavior."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            # Create first instance
            cg1 = CooccurrenceGraph(
                sqlite_db_path=tmp.name,
                entity_extractor=MockEntityExtractor(),
                entity_mapper=MockMapper(),
            )
            cg1.fit(["Test doc."])

            # Create second instance with overwrite
            cg2 = CooccurrenceGraph(
                sqlite_db_path=tmp.name,
                on_existing_db="overwrite",
            )
            self.assertEqual(str(cg2._engine.url), "sqlite:///" + tmp.name)


if __name__ == "__main__":
    unittest.main()
