import logging
import os
from datetime import datetime, date
from typing import Literal

import pandas as pd
from sqlalchemy import text

from narrativegraph.db.engine import (
    get_engine,
)
from narrativegraph.dto.cooccurrences import CoOccurrenceDetails
from narrativegraph.dto.documents import Document
from narrativegraph.dto.entities import EntityDetails
from narrativegraph.dto.filter import GraphFilter
from narrativegraph.dto.predicates import PredicateDetails
from narrativegraph.dto.relations import RelationDetails
from narrativegraph.nlp.extraction import TripletExtractor
from narrativegraph.nlp.mapping import Mapper
from narrativegraph.nlp.pipeline import Pipeline
from narrativegraph.server.backgroundserver import BackgroundServer
from narrativegraph.service import QueryService

logging.basicConfig(level=logging.INFO)
_logger = logging.getLogger("narrativegraph")
_logger.setLevel(logging.INFO)


class NarrativeGraph:
    def __init__(
        self,
        triplet_extractor: TripletExtractor = None,
        entity_mapper: Mapper = None,
        relation_mapper: Mapper = None,
        sqlite_db_path: str = None,
        on_existing_db: Literal["stop", "overwrite", "reuse"] = "stop",
    ):
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

        self._engine = get_engine(sqlite_db_path)
        self._db_service = QueryService(self._engine)
        self._pipeline = Pipeline(
            self._engine,
            triplet_extractor=triplet_extractor,
            entity_mapper=entity_mapper,
            relation_mapper=relation_mapper,
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
        self._pipeline.run(
            docs,
            doc_ids=doc_ids,
            timestamps=timestamps,
            categories=categories,
        )
        return self

    @property
    def entities_(self) -> pd.DataFrame:
        return self._db_service.entities.as_df()

    @property
    def predicates_(self) -> pd.DataFrame:
        return self._db_service.predicates.as_df()

    @property
    def relations_(self) -> pd.DataFrame:
        return self._db_service.relations.as_df()

    @property
    def co_occurrences_(self) -> pd.DataFrame:
        return self._db_service.co_occurrences.as_df()

    @property
    def documents_(self) -> pd.DataFrame:
        return self._db_service.documents.as_df()

    @property
    def triplets_(self) -> pd.DataFrame:
        return self._db_service.triplets.as_df()

    def get_entities(
        self, ids: list[int] = None, limit: int = None
    ) -> list[EntityDetails]:
        return self._db_service.entities.get_multiple(ids=ids, limit=limit)

    def get_predicates(
        self, ids: list[int] = None, limit: int = None
    ) -> list[PredicateDetails]:
        return self._db_service.predicates.get_multiple(ids=ids, limit=limit)

    def get_relations(
        self, ids: list[int] = None, limit: int = None
    ) -> list[RelationDetails]:
        return self._db_service.relations.get_multiple(ids=ids, limit=limit)

    def get_co_occurrences(
        self, ids: list[int] = None, limit: int = None
    ) -> list[CoOccurrenceDetails]:
        return self._db_service.co_occurrences.get_multiple(ids=ids, limit=limit)

    def get_documents(self, ids: list[int] = None, limit: int = None) -> list[Document]:
        return self._db_service.documents.get_multiple(ids=ids, limit=limit)

    def find_communities(
        self, graph_filter: GraphFilter = None
    ) -> list[list[int]]:
        return self._db_service.graph.find_communities(
            graph_filter=graph_filter
        )

    def serve_visualizer(
        self,
        port: int = 8001,
        block: bool = True,
        autostart: bool = True,
    ):
        """
        Serve the visualizer application.

        :param port: The port number on which the visualizer should be served.
        :param block: If True (default), the function will block until the server is stopped.
        If False, the server will run in the background.
        :param autostart: If True (default), the server is started automatically. Only relevant
        for background servers.


        :return: None
        """
        server = BackgroundServer(self._db_service.engine, port=port)
        if autostart:
            server.start(block=block)
        if not block:
            return server
        else:
            return None

    def save_to_file(self, file_path: str, overwrite: bool = True):
        """Save in-memory database to file"""
        if os.path.exists(file_path) and not overwrite:
            raise FileExistsError(
                f"File exists: {file_path}. Set overwrite=True to replace."
            )

        if str(self._engine.url) == "sqlite:///:memory:":
            with self._db_service.get_session_context() as session:
                session.execute(text(f"VACUUM main INTO '{file_path}'"))
        else:
            raise ValueError("Database is already file-based.")

    @classmethod
    def load(cls, sqlite_db_path: str):
        if not os.path.exists(sqlite_db_path):
            raise FileNotFoundError(f"Database not found: {sqlite_db_path}")
        return cls(sqlite_db_path=sqlite_db_path, on_existing_db="reuse")
