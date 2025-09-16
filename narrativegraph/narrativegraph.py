import logging
import os
from datetime import datetime, date

import pandas as pd
from tqdm import tqdm

from narrativegraph.db.dtos import Node
from narrativegraph.db.service.common import DbService
from narrativegraph.db.service.query import QueryService
from narrativegraph.extraction.spacy.common import SpacyTripletExtractor
from narrativegraph.extraction.spacy.dependencygraph import DependencyGraphExtractor
from narrativegraph.mapping.common import Mapper
from narrativegraph.mapping.linguistic import StemmingMapper, SubgramStemmingMapper
from narrativegraph.pipeline.pipeline import Pipeline
from narrativegraph.server.backgroundserver import BackgroundServer
from narrativegraph.utils.transform import normalize_categories

logging.basicConfig(level=logging.INFO)
_logger = logging.getLogger("narrativegraph")
_logger.setLevel(logging.INFO)


class NarrativeGraph:
    def __init__(
        self,
        triplet_extractor: SpacyTripletExtractor = None,
        entity_mapper: Mapper = None,
        relation_mapper: Mapper = None,
        sqlite_db_path: str = None,
        overwrite_db: bool = False,
    ):
        # Data storage
        if sqlite_db_path is not None and os.path.exists(sqlite_db_path):
            if overwrite_db:
                # TODO: should not happen here because one cannot re-use the DB in a new object
                _logger.info("Overwriting SQLite DB %s", sqlite_db_path)
                os.remove(sqlite_db_path)
            else:
                raise FileExistsError("SQLite database already exists")
        self._sql_db_path = sqlite_db_path or "sqlite:///:memory:"
        self._db_service = QueryService(db_filepath=sqlite_db_path)

        self._pipeline = Pipeline(
            triplet_extractor=triplet_extractor,
            entity_mapper=entity_mapper,
            relation_mapper=relation_mapper,
            sqlite_db_path=sqlite_db_path
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

        :param docs:
        :param doc_ids:
        :param timestamps:
        :param categories: Categories that the documents belong to. They be provided in multiple ways.

        :return:
        """
        self._pipeline.run(
            docs,
            doc_ids=doc_ids,
            timestamps=timestamps,
            categories=categories,
        )
        return self

    @property
    def entities(self) -> list[Node]:
        return self._db_service.get_entities()

    @property
    def entities_df(self) -> pd.DataFrame:
        return self._db_service.get_entities_df()

    def serve_visualizer(
        self, port: int = 8001, autostart: bool = True, block: bool = True
    ):
        """
        Serve the visualizer application.

        :param port: The port number on which the visualizer should be served. Defaults to 8001.
        :param autostart: If True, the server is started automatically. Defaults to True.
        :param block: If True, the function will block until the server is stopped. If False, the server will run in the background. Defaults to True.

        :return: None
        """
        server = BackgroundServer(self._db_service.engine, port=port)
        if autostart:
            server.start(block=block)
        if not block:
            return server
        else:
            return None
