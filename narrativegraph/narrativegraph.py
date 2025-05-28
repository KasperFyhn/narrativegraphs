import asyncio
import logging
import os
import threading
import time
from datetime import datetime
from string import punctuation
from threading import Event

import uvicorn
from tqdm import tqdm

from narrativegraph.db.orms import EntityOrm
from narrativegraph.db.service import DbService
from narrativegraph.extraction.common import TripletExtractor
from narrativegraph.extraction.spacy import DependencyGraphExtractor
from narrativegraph.mapping.common import Mapper
from narrativegraph.mapping.linguistic import StemmingMapper, SubgramStemmingMapper
from narrativegraph.server.main import app
from narrativegraph.visualization.common import Edge, Node
from narrativegraph.visualization.plotly import GraphPlotter

logging.basicConfig(level=logging.INFO)
_logger = logging.getLogger("narrativegraph")
_logger.setLevel(logging.INFO)


class NarrativeGraph:
    def __init__(self, triplet_extractor: TripletExtractor = None, entity_mapper: Mapper = None,
                 relation_mapper: Mapper = None, sqlite_db_path: str = None):
        # Analysis components
        self._triplet_extractor = triplet_extractor or DependencyGraphExtractor()
        self._entity_mapper = entity_mapper or StemmingMapper()
        self._relation_mapper = relation_mapper or SubgramStemmingMapper()

        # Data storage
        self._sql_db_path = sqlite_db_path or "sqlite:///:memory:"
        self._db_service = DbService(db_filepath=sqlite_db_path)

        self.predicate_mapping = None
        self.entity_mapping = None

        # Visualizer server
        self._server_thread = None
        self._server: uvicorn.Server | None = None


    def fit(self, docs: list[str], doc_ids: list[int | str] = None, timestamps: list[datetime] = None,
            categories: list[str] = None):
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
            self._db_service.add_triplets(doc.id, doc_triplets, category=doc.category)

        _logger.info(f"Mapping entities and relations")
        triplets = self._db_service.get_triplets()
        entities = [entity for triplet in triplets
                    for entity in [triplet.subj_span_text, triplet.obj_span_text]]
        self.entity_mapping = self._entity_mapper.create_mapping(entities)

        predicates = [triplet.pred_span_text for triplet in triplets]
        self.predicate_mapping = self._entity_mapper.create_mapping(predicates)

        _logger.info(f"Mapping triplets")
        self._db_service.map_triplets(self.entity_mapping, self.predicate_mapping)

    def show_graph(self, max_edges: int = 25):
        _logger.info(f"Showing graph")
        relations = self._db_service.get_relations(n=max_edges)
        entities: dict[int, EntityOrm] = {}
        for relation in relations:
            entities[relation.subject_id] = relation.subject
            entities[relation.object_id] = relation.object

        edges = [Edge(
            source_id=relation.subject_id,
            target_id=relation.object_id,
            label=relation.label,
            categories=relation.categories.split(',')
        )
            for relation in relations]
        nodes = [Node(
            id=entity.id,
            label=''.join(c for c in entity.label if c.isalnum() or c in " '-"),
            categories=entity.categories.split(',')
        )
            for entity in entities.values()]

        GraphPlotter(
            edges=edges,
            nodes=nodes,
        ).plot()

    def serve_visualizer(self, port: int = 8001):

        if self._server_thread is not None and self._server_thread.is_alive():
            _logger.warning(f"Server already running on port {self._server.config.port}!")
            return

        _logger.info(f"Serving visualizer on port {port}")

        # Set environment variables
        os.environ['DB_PATH'] = self._sql_db_path

        async def run_server():
            config = uvicorn.Config(app, port=port, log_level="info")
            server = uvicorn.Server(config)

            # Store server reference for shutdown
            self._server = server

            try:
                await server.serve()
            except asyncio.CancelledError:
                _logger.info("Server cancelled")

        def run_server_thread():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            try:
                loop.run_until_complete(run_server())
            except Exception as e:
                _logger.error(f"Server error: {e}")
            finally:
                loop.close()

        if self._server_thread is None:
            self._server_thread = threading.Thread(target=run_server_thread, daemon=True)
            self._server_thread.start()

    def stop_server(self):
        if self._server:
            _logger.info("Stopping server...")

            # Shutdown the uvicorn server
            self._server.should_exit = True

            if self._server_thread and self._server_thread.is_alive():
                self._server_thread.join(timeout=10)

            if self._server_thread and self._server_thread.is_alive():
                _logger.warning("Server did not stop successfully!")
            else:
                _logger.info("Server stopped successfully")
                self._server_thread = None
                self._server = None
        else:
            _logger.error("Server is not running!")