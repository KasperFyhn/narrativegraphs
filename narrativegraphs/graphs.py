import logging
import os
from datetime import date, datetime
from typing import TYPE_CHECKING, Literal

import networkx as nx
import pandas as pd
from sqlalchemy import text

from narrativegraphs.db.engine import get_engine
from narrativegraphs.nlp.entities.common import EntityExtractor
from narrativegraphs.nlp.mapping import Mapper
from narrativegraphs.nlp.pipeline import CooccurrencePipeline, Pipeline
from narrativegraphs.nlp.triplets import TripletExtractor
from narrativegraphs.nlp.tuplets.common import CooccurrenceExtractor
from narrativegraphs.service import QueryService

if TYPE_CHECKING:
    from narrativegraphs.server.backgroundserver import BackgroundServer

logging.basicConfig(level=logging.INFO)
_logger = logging.getLogger("narrativegraphs")
_logger.setLevel(logging.INFO)


class BaseGraph(QueryService):
    """Base class for graph implementations.

    Provides shared functionality for database management, persistence,
    visualization, and access to entities, cooccurrences, and documents.
    """

    def __init__(
        self,
        sqlite_db_path: str = None,
        on_existing_db: Literal["stop", "overwrite", "reuse"] = "stop",
    ):
        """Initialize the base graph.

        Args:
            sqlite_db_path: Path to SQLite database file. If None, uses in-memory DB.
            on_existing_db: Behavior when database exists:
                - "stop": Raise error if DB contains data
                - "overwrite": Delete existing DB
                - "reuse": Use existing DB data
        """
        if sqlite_db_path and os.path.exists(sqlite_db_path):
            if on_existing_db == "overwrite":
                os.remove(sqlite_db_path)
            elif on_existing_db == "stop":
                temp_service = QueryService(get_engine(sqlite_db_path))
                if len(temp_service.documents.get_multiple(limit=1)) > 0:
                    raise FileExistsError(
                        f"Database contains data. Use {self.__class__.__name__}.load() "
                        "or set on_existing_db to 'overwrite' or 'reuse'."
                    )

        super().__init__(get_engine(sqlite_db_path))

    @property
    def entities_(self) -> pd.DataFrame:
        """Entities as a pandas DataFrame."""
        return self.entities.as_df()

    @property
    def entity_mentions_(self) -> pd.DataFrame:
        """Entity mentions as a pandas DataFrame."""
        return self.mentions.as_df()

    @property
    def cooccurrences_(self) -> pd.DataFrame:
        """Co-occurrences as a pandas DataFrame."""
        return self.cooccurrences.as_df()

    @property
    def documents_(self) -> pd.DataFrame:
        """Documents as a pandas DataFrame."""
        return self.documents.as_df()

    @property
    def cooccurrence_graph_(self) -> nx.Graph:
        """The full cooccurrence graph as an undirected NetworkX graph."""
        cg = self.graph.get_graph("cooccurrence")
        g = nx.Graph()
        g.add_nodes_from((n.id, n) for n in cg.nodes)
        g.add_edges_from((e.from_id, e.to_id) for e in cg.edges)
        return g

    def serve_visualizer(
        self,
        port: int = 8001,
        block: bool = True,
        autostart: bool = True,
    ) -> "BackgroundServer | None":
        """Serve the visualizer application.

        Args:
            port: The port that the visualizer should be served on.
            block: If True (default), the function will block until the server is
                stopped. If False, the server will run in the background.
            autostart: If True (default), the server is started automatically. Only
                relevant for background servers.

        Returns:
            If not blocking, return a BackgroundServer object. If blocking, return
                None after termination.
        """
        from narrativegraphs.server.backgroundserver import BackgroundServer

        server = BackgroundServer(self._engine, port=port)
        if autostart:
            server.start(block=block)
        if not block:
            return server
        else:
            return None

    def save_to_file(self, file_path: str, overwrite: bool = False):
        """Save in-memory database to file.

        Args:
            file_path: Path to save the database to.
            overwrite: If True, overwrite existing file. If False, raise error.
        """
        if not file_path.endswith(".db"):
            file_path += ".db"

        if os.path.exists(file_path):
            if not overwrite:
                raise FileExistsError(
                    f"File exists: {file_path}. Set overwrite=True to replace."
                )
            else:
                os.remove(file_path)

        with self.get_session_context() as session:
            session.execute(text(f"VACUUM main INTO '{file_path}'"))

    @classmethod
    def load(cls, file_path: str):
        """Load from a SQLite database file.

        Args:
            file_path: Path to a SQLite database to load from.

        Returns:
            A loaded object backed by the database.
        """
        if not file_path.endswith(".db"):
            file_path += ".db"

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Database not found: {file_path}")
        return cls(sqlite_db_path=file_path, on_existing_db="reuse")


class CooccurrenceGraph(BaseGraph):
    """Co-occurrence graph without triplet extraction.

    CooccurrenceGraph extracts entities directly from text and builds an
    undirected co-occurrence graph. Unlike NarrativeGraph, it does not
    extract subject-predicate-object triplets or build a relation graph.

    Use this when you only need entity co-occurrence analysis without
    the overhead of triplet extraction.
    """

    def __init__(
        self,
        entity_extractor: EntityExtractor = None,
        cooccurrence_extractor: CooccurrenceExtractor = None,
        entity_mapper: Mapper = None,
        sqlite_db_path: str = None,
        on_existing_db: Literal["stop", "overwrite", "reuse"] = "stop",
        n_cpu: int = 1,
    ):
        """Initialize a CooccurrenceGraph.

        Args:
            entity_extractor: Extractor for entities (default: SpacyEntityExtractor).
            cooccurrence_extractor: Extractor for entity co-occurrences.
            entity_mapper: Mapper for entity normalization.
            sqlite_db_path: Path to SQLite database file. If None, uses in-memory DB.
            on_existing_db: Behavior when database exists:
                - "stop": Raise error if DB contains data
                - "overwrite": Delete existing DB
                - "reuse": Use existing DB data
            n_cpu: Number of CPUs for parallel processing (-1 for all).
        """
        super().__init__(sqlite_db_path, on_existing_db)
        self._pipeline = CooccurrencePipeline(
            self._engine,
            entity_extractor=entity_extractor,
            cooccurrence_extractor=cooccurrence_extractor,
            entity_mapper=entity_mapper,
            n_cpu=n_cpu,
        )

    def fit(
        self,
        docs: list[str],
        doc_ids: list[int | str] = None,
        timestamps: list[datetime | date] = None,
        timestamps_ordinal: list[int] = None,
        categories: (
            list[str | list[str]]
            | dict[str, list[str | list[str]]]
            | list[dict[str, str | list[str]]]
        ) = None,
    ) -> "CooccurrenceGraph":
        """Fit a co-occurrence graph from documents.

        Args:
            docs: Required argument, a list of documents as strings.
            doc_ids: Optional list of document ids. Same length as docs.
            timestamps: Optional list of document timestamps. Same length as docs.
            timestamps_ordinal: Optional list of document timestamps as an arbitrary
                integer, e.g. page, section or chapter number. Same length as docs.
            categories: Optional list of document categories. Supports single or
                multiple categories. A document can have a single or multiple labels
                per category.

        Returns:
            A fitted CooccurrenceGraph instance.
        """
        self._pipeline.run(
            docs,
            doc_ids=doc_ids,
            timestamps=timestamps,
            timestamps_ordinal=timestamps_ordinal,
            categories=categories,
        )
        return self

    @classmethod
    def load(cls, file_path: str) -> "CooccurrenceGraph":
        """Load a CooccurrenceGraph from a SQLite database file.

        Args:
            file_path: Path to a SQLite database to load a CooccurrenceGraph from.

        Returns:
            A CooccurrenceGraph object.
        """
        return super().load(file_path)  # noqa


class NarrativeGraph(BaseGraph):
    """Full narrative graph with triplet extraction, relations, and co-occurrences.

    NarrativeGraph extracts subject-predicate-object triplets from text documents
    and builds both a directed relation graph and an undirected co-occurrence graph.
    """

    def __init__(
        self,
        triplet_extractor: TripletExtractor = None,
        cooccurrence_extractor: CooccurrenceExtractor = None,
        entity_mapper: Mapper = None,
        predicate_mapper: Mapper = None,
        sqlite_db_path: str = None,
        on_existing_db: Literal["stop", "overwrite", "reuse"] = "stop",
        n_cpu: int = 1,
    ):
        """Initialize a NarrativeGraph.

        Args:
            triplet_extractor: Extractor for subject-predicate-object triplets.
            cooccurrence_extractor: Extractor for entity co-occurrences.
            entity_mapper: Mapper for entity normalization.
            predicate_mapper: Mapper for predicate normalization.
            sqlite_db_path: Path to SQLite database file. If None, uses in-memory DB.
            on_existing_db: Behavior when database exists:
                - "stop": Raise error if DB contains data
                - "overwrite": Delete existing DB
                - "reuse": Use existing DB data
            n_cpu: Number of CPUs for parallel processing (-1 for all).
        """
        super().__init__(sqlite_db_path, on_existing_db)
        self._pipeline = Pipeline(
            self._engine,
            triplet_extractor=triplet_extractor,
            cooccurrence_extractor=cooccurrence_extractor,
            entity_mapper=entity_mapper,
            predicate_mapper=predicate_mapper,
            n_cpu=n_cpu,
        )

    def fit(
        self,
        docs: list[str],
        doc_ids: list[int | str] = None,
        timestamps: list[datetime | date] = None,
        categories: (
            list[str | list[str]]
            | dict[str, list[str | list[str]]]
            | list[dict[str, str | list[str]]]
        ) = None,
    ) -> "NarrativeGraph":
        """
        Fit a narrative graph from documents. The docs can be accompanied by lists with
        the same length of IDs, timestamps and categories.

        Args:
            docs: Required argument, a list of documents as strings.
            doc_ids: Optional list of document ids. Same length as docs.
            timestamps: Optional list of document timestamps. Same length as docs.
            categories: Optional list of document categories. Supports single or
                multiple categories. A document can have a single or multiple labels
                per category. See further down for examples.

        Returns:
            A fitted NarrativeGraph instance.

        """
        self._pipeline.run(
            docs,
            doc_ids=doc_ids,
            timestamps=timestamps,
            categories=categories,
        )
        return self

    @property
    def predicates_(self) -> pd.DataFrame:
        """Predicates as a pandas DataFrame."""
        return self.predicates.as_df()

    @property
    def relations_(self) -> pd.DataFrame:
        """Relations as a pandas DataFrame."""
        return self.relations.as_df()

    @property
    def triplets_(self) -> pd.DataFrame:
        """Triplets as a pandas DataFrame."""
        return self.triplets.as_df()

    @property
    def relation_graph_(self) -> nx.DiGraph:
        """The full relation graph as a directed NetworkX graph."""
        rg = self.graph.get_graph("relation")
        g = nx.DiGraph()
        g.add_nodes_from((n.id, n) for n in rg.nodes)
        g.add_edges_from((e.from_id, e.to_id, e) for e in rg.edges)
        return g

    @classmethod
    def load(cls, file_path: str) -> "NarrativeGraph":
        """

        Args:
            file_path: path to a SQLite database to load a NarrativeGraph from.

        Returns:
            A NarrativeGraph object
        """
        return super().load(file_path)  # noqa
