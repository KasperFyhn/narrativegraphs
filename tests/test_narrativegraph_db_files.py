import tempfile
from unittest.mock import Mock, patch

import pytest

from narrativegraphs import NarrativeGraph
from tests.mocks import MockMapper, MockTripletExtractor


class TestNarrativeGraphFileHandling:
    def test_init_memory_db_default(self):
        """Test default initialization creates in-memory database"""
        ng = NarrativeGraph()
        assert str(ng._engine.url) == "sqlite:///:memory:"

    def test_init_file_db_new(self):
        """Test initialization with new file database"""
        with tempfile.NamedTemporaryFile(delete=True) as tmp:
            ng = NarrativeGraph(sqlite_db_path=tmp.name)
            assert str(ng._engine.url) == "sqlite:///" + tmp.name

    def test_init_file_db_exists_empty_default_stop(self):
        """Test initialization with existing empty database (stop behavior)"""
        with tempfile.NamedTemporaryFile() as tmp:
            # Create empty database file
            NarrativeGraph(sqlite_db_path=tmp.name)

            # Should work with existing empty database
            ng = NarrativeGraph(sqlite_db_path=tmp.name)
            assert str(ng._engine.url) == "sqlite:///" + tmp.name

    @patch("narrativegraphs.narrativegraph.QueryService")
    def test_init_file_db_exists_with_data_stop_raises(self, mock_query_service):
        """Test initialization with existing database containing data raises error"""
        with tempfile.NamedTemporaryFile() as tmp:
            mock_service = Mock()
            mock_service.documents.get_docs.return_value = [Mock()]
            mock_query_service.return_value = mock_service

            with pytest.raises(FileExistsError, match="Database contains data"):
                NarrativeGraph(sqlite_db_path=tmp.name, on_existing_db="stop")

    @patch("narrativegraphs.narrativegraph.QueryService")
    def test_init_file_db_exists_reuse(self, mock_query_service):
        """Test reuse behavior with existing database"""
        with tempfile.NamedTemporaryFile() as tmp:
            # Mock service to return data
            mock_service = Mock()
            mock_service.docs.get_docs.return_value = [Mock()]  # Has data
            mock_query_service.return_value = mock_service

            ng = NarrativeGraph(sqlite_db_path=tmp.name, on_existing_db="reuse")
            assert str(ng._engine.url) == "sqlite:///" + tmp.name

    def test_load_file_exists(self):
        """Test loading existing database file"""
        with tempfile.NamedTemporaryFile(suffix=".db") as tmp:
            # Create database
            NarrativeGraph(sqlite_db_path=tmp.name)

            # Load existing database
            ng = NarrativeGraph.load(tmp.name)
            assert str(ng._engine.url) == "sqlite:///" + tmp.name

    def test_load_file_not_exists(self):
        """Test loading non-existent database file raises error"""
        with pytest.raises(FileNotFoundError, match="Database not found"):
            NarrativeGraph.load("nonexistent.db")

    def test_save_to_file_existing_file_no_overwrite(self):
        """Test saving to existing file without overwrite raises error"""
        ng = NarrativeGraph()  # Memory database

        with tempfile.NamedTemporaryFile(suffix=".db") as tmp:
            with pytest.raises(FileExistsError, match="File exists"):
                ng.save_to_file(tmp.name, overwrite=False)

    def test_save_to_file_from_file_db_raises(self):
        """Test saving file-based database raises error"""
        with tempfile.NamedTemporaryFile() as tmp:
            ng = NarrativeGraph(sqlite_db_path=tmp.name)

            with tempfile.NamedTemporaryFile() as target:
                with pytest.raises(ValueError, match="Database is already file-based"):
                    ng.save_to_file(target.name)

    def test_save_and_load(self):
        """Integration test: create, fit, save, and load database"""
        # Create and populate in-memory database
        ng1 = NarrativeGraph(
            triplet_extractor=MockTripletExtractor(),
            entity_mapper=MockMapper(),
            predicate_mapper=MockMapper(),
        )
        ng1.fit(["Test document 1", "Test document 2"])

        # Save to file
        with tempfile.NamedTemporaryFile(suffix=".db") as tmp:
            ng1.save_to_file(tmp.name)

            # Load from file
            ng2 = NarrativeGraph.load(tmp.name)

            # Verify data persisted
            docs1 = ng1.documents_
            docs2 = ng2.documents_

            assert len(docs1) == len(docs2)
            assert len(docs1) == 2


if __name__ == "__main__":
    pytest.main([__file__])
