import logging
import os
from datetime import datetime

from tqdm import tqdm

from narrativegraph.db.service import DbService
from narrativegraph.extraction.spacy.common import SpacyTripletExtractor
from narrativegraph.extraction.spacy.dependencygraph import DependencyGraphExtractor
from narrativegraph.mapping.common import Mapper
from narrativegraph.mapping.linguistic import StemmingMapper, SubgramStemmingMapper
from narrativegraph.server.backgroundserver import BackgroundServer

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
        # Analysis components
        self._triplet_extractor = triplet_extractor or DependencyGraphExtractor()
        self._entity_mapper = entity_mapper or StemmingMapper()
        self._relation_mapper = relation_mapper or SubgramStemmingMapper()

        # Data storage
        if sqlite_db_path is not None and os.path.exists(sqlite_db_path):
            if overwrite_db:
                # TODO: should not happen here because one cannot re-use the DB in a new object
                _logger.info("Overwriting SQLite DB %s", sqlite_db_path)
                os.remove(sqlite_db_path)
            else:
                raise FileExistsError("SQLite database already exists")
        self._sql_db_path = sqlite_db_path or "sqlite:///:memory:"
        self._db_service = DbService(db_filepath=sqlite_db_path)

        self.predicate_mapping = None
        self.entity_mapping = None

    def fit(self, docs: list[str], doc_ids: list[int | str] = None, timestamps: list[datetime] = None,
            categories: list[str] = None) -> "NarrativeGraph":
        _logger.info(f"Adding {len(docs)} documents to database")
        self._db_service.add_documents(
            docs, doc_ids=doc_ids, timestamps=timestamps, categories=categories)

        _logger.info(f"Extracting triplets")
        doc_orms = self._db_service.get_docs()
        extracted_triplets = self._triplet_extractor.batch_extract(
            [d.text for d in doc_orms]
        )
        docs_and_triplets = zip(doc_orms, extracted_triplets)
        if _logger.isEnabledFor(logging.INFO):
            docs_and_triplets = tqdm(docs_and_triplets,
                                     desc="Extracting triplets",
                                     total=len(docs))
        for doc, doc_triplets in docs_and_triplets:
            self._db_service.add_triplets(doc.id, doc_triplets, category=doc.category,
                                          timestamp=doc.timestamp)

        _logger.info(f"Mapping entities and relations")
        triplets = self._db_service.get_triplets()
        entities = [entity for triplet in triplets
                    for entity in [triplet.subj_span_text, triplet.obj_span_text]]
        self.entity_mapping = self._entity_mapper.create_mapping(entities)

        predicates = [triplet.pred_span_text for triplet in triplets]
        self.predicate_mapping = self._entity_mapper.create_mapping(predicates)

        _logger.info(f"Mapping triplets")
        self._db_service.map_triplets(self.entity_mapping, self.predicate_mapping)

        return self

    def serve_visualizer(self, port: int = 8001, autostart: bool = True, block: bool = True):
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
