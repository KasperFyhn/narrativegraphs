import logging
import os
from datetime import date, datetime
from typing import Literal

import networkx as nx
import pandas as pd
import spacy
from sqlalchemy import text

from narrativegraphs.db.engine import (
    get_engine,
)
from narrativegraphs.nlp.extraction import TripletExtractor
from narrativegraphs.nlp.extraction.cooccurrences import CooccurrenceExtractor
from narrativegraphs.nlp.mapping import Mapper
from narrativegraphs.nlp.pipeline import Pipeline
from narrativegraphs.server.backgroundserver import BackgroundServer
from narrativegraphs.service import QueryService

logging.basicConfig(level=logging.INFO)
_logger = logging.getLogger("narrativegraphs")
_logger.setLevel(logging.INFO)


class NarrativeGraph(QueryService):
    def __init__(
        self,
        triplet_extractor: TripletExtractor = None,
        cooccurrence_extractor: CooccurrenceExtractor = None,
        entity_mapper: Mapper = None,
        predicate_mapper: Mapper = None,
        sqlite_db_path: str = None,
        on_existing_db: Literal["stop", "overwrite", "reuse"] = "stop",
        n_cpu: int = -1,
    ):
        """

        Args:
            triplet_extractor:
            cooccurrence_extractor:
            entity_mapper:
            predicate_mapper:
            sqlite_db_path:
            on_existing_db:
            n_cpu:
        """
        # Check if DB exists and has data
        if sqlite_db_path and os.path.exists(sqlite_db_path):
            if on_existing_db == "overwrite":
                os.remove(sqlite_db_path)
            elif on_existing_db == "stop":
                temp_service = QueryService(get_engine(sqlite_db_path))
                if len(temp_service.documents.get_docs(limit=1)) > 0:
                    raise FileExistsError(
                        "Database contains data. Use NarrativeGraph.load() or set "
                        "on_existing_db to 'overwrite' or 'reuse'."
                    )

        super().__init__(get_engine(sqlite_db_path))
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
    def entities_(self) -> pd.DataFrame:
        spacy.blank("en")
        return self.entities.as_df()

    @property
    def predicates_(self) -> pd.DataFrame:
        return self.predicates.as_df()

    @property
    def relations_(self) -> pd.DataFrame:
        return self.relations.as_df()

    @property
    def cooccurrences_(self) -> pd.DataFrame:
        return self.cooccurrences.as_df()

    @property
    def documents_(self) -> pd.DataFrame:
        return self.documents.as_df()

    @property
    def triplets_(self) -> pd.DataFrame:
        return self.triplets.as_df()

    @property
    def relation_graph_(self) -> nx.DiGraph:
        """The full relation graph as a directed NetworkX graph."""
        rg = self.graph.get_graph("relation")
        g = nx.DiGraph()
        g.add_nodes_from((n.id, n) for n in rg.nodes)
        g.add_edges_from((e.from_id, e.to_id, e) for e in rg.edges)
        return g

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
    ) -> BackgroundServer | None:
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
        server = BackgroundServer(self._engine, port=port)
        if autostart:
            server.start(block=block)
        if not block:
            return server
        else:
            return None

    def save_to_file(self, file_path: str, overwrite: bool = True):
        """Save in-memory database to file"""
        if not file_path.endswith(".db"):
            file_path += ".db"

        if os.path.exists(file_path):
            if not overwrite:
                raise FileExistsError(
                    f"File exists: {file_path}. Set overwrite=True to replace."
                )
            else:
                os.remove(file_path)

        if str(self._engine.url) == "sqlite:///:memory:":
            with self.get_session_context() as session:
                session.execute(text(f"VACUUM main INTO '{file_path}'"))
        else:
            raise ValueError("Database is already file-based.")

    @classmethod
    def load(cls, file_path: str) -> "NarrativeGraph":
        """

        Args:
            file_path: path to a SQLite database to load a NarrativeGraph from.

        Returns:
            A NarrativeGraph object
        """
        if not file_path.endswith(".db"):
            file_path += ".db"

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Database not found: {file_path}")
        return cls(sqlite_db_path=file_path, on_existing_db="reuse")
