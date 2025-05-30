import asyncio
import logging
import time
from datetime import datetime

import nest_asyncio
import uvicorn
from tqdm import tqdm
from uvicorn import Server

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
        self._server_task = None
        self._server: Server = None

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

    def serve_visualizer(self, port: int = 8001, block: bool = True):
        """
        Serve the visualizer application.

        :param port: The port number on which the visualizer should be served. Defaults to 8001.

        :param block: If True, the function will block until the server is stopped. If False, the server will run in the background. Defaults to True.

        :return: None
        """

        # Check if server is already running

        if self._server_task is not None and not self._server_task.done():
            _logger.warning("Server already running! Stop it first with stop_visualizer()")
            return

        _logger.info(f"Serving visualizer on port {port}")

        nest_asyncio.apply()

        async def run_server():
            config = uvicorn.Config(app, port=port, log_level="info")
            server = uvicorn.Server(config)
            self._server = server

            try:
                app.state.db_service = self._db_service
                await server.serve()
            except asyncio.CancelledError:
                _logger.info("Server cancelled")

        if block:
            try:
                asyncio.run(run_server())
            except KeyboardInterrupt:
                self._server = None
                _logger.info("Server stopped by user")
        else:
            # Create background task
            self._server_task = asyncio.create_task(run_server())
            _logger.info(f"Server started in background on port {port}")

    async def stop_visualizer(self):
        """
        Asynchronously stops the background visualizer server.

        Example usage: ``await narrative_graph.stop_visualizer()``

        """
        if self._server_task is not None and not self._server_task.done():
            self._server.should_exit = True

            try:
                # Wait up to 5 seconds for graceful shutdown
                await asyncio.wait_for(self._server_task, timeout=5.0)
            except asyncio.TimeoutError:
                _logger.warning("Server didn't shut down gracefully, forcing cancellation")
                self._server_task.cancel()
                try:
                    await self._server_task
                except asyncio.CancelledError:
                    pass

            self._server = None
            self._server_task = None
            _logger.info("Background server stopped")
        else:
            _logger.info("No server running")
