import logging
from datetime import date, datetime

from sqlalchemy import Engine
from tqdm import tqdm

from narrativegraphs.nlp.extraction import EntityExtractor, SpacyEntityExtractor
from narrativegraphs.nlp.extraction.cooccurrences import (
    ChunkCooccurrenceExtractor,
    CooccurrenceExtractor,
)
from narrativegraphs.nlp.mapping import Mapper
from narrativegraphs.nlp.mapping.linguistic import SubgramStemmingMapper
from narrativegraphs.service import PopulationService
from narrativegraphs.utils.transform import normalize_categories

logging.basicConfig(level=logging.INFO)
_logger = logging.getLogger("narrativegraphs.cooccurrence_pipeline")
_logger.setLevel(logging.INFO)


class CooccurrencePipeline:
    """Simplified pipeline for co-occurrence extraction without triplet extraction.

    This pipeline extracts entities directly using an EntityExtractor, then
    builds co-occurrence relationships between them. It skips the triplet
    extraction and predicate mapping steps used in the full Pipeline.
    """

    def __init__(
        self,
        engine: Engine,
        entity_extractor: EntityExtractor = None,
        cooccurrence_extractor: CooccurrenceExtractor = None,
        entity_mapper: Mapper = None,
        n_cpu: int = 1,
    ):
        """Initialize the co-occurrence pipeline.

        Args:
            engine: SQLAlchemy engine for database access
            entity_extractor: Extractor for entities (default: SpacyEntityExtractor)
            cooccurrence_extractor: Extractor for co-occurrences
                (default: ChunkCooccurrenceExtractor)
            entity_mapper: Mapper for entity normalization
                (default: SubgramStemmingMapper)
            n_cpu: Number of CPUs for parallel processing
        """
        self._entity_extractor = entity_extractor or SpacyEntityExtractor()
        self._cooccurrence_extractor = (
            cooccurrence_extractor or ChunkCooccurrenceExtractor()
        )
        self._entity_mapper = entity_mapper or SubgramStemmingMapper("noun")

        self.n_cpu = n_cpu

        self._db_service = PopulationService(engine)
        self.entity_mapping = None

    def run(
        self,
        docs: list[str],
        doc_ids: list[int | str] = None,
        timestamps: list[datetime | date] = None,
        categories: (
            list[str | list[str]]
            | dict[str, list[str | list[str]]]
            | list[dict[str, str | list[str]]]
        ) = None,
    ):
        """Run the co-occurrence pipeline on a set of documents.

        Args:
            docs: List of document texts
            doc_ids: Optional list of document identifiers
            timestamps: Optional list of document timestamps
            categories: Optional document categorization

        Returns:
            self for method chaining
        """
        with self._db_service.get_session_context():
            _logger.info(f"Adding {len(docs)} documents to database")
            if categories is not None:
                categories = normalize_categories(categories)

            self._db_service.add_documents(
                docs,
                doc_ids=doc_ids,
                timestamps=timestamps,
                categories=categories,
            )

            _logger.info("Extracting entities")
            doc_orms = self._db_service.get_docs()
            extracted_entities = self._entity_extractor.batch_extract(
                [d.text for d in doc_orms], n_cpu=self.n_cpu
            )
            docs_and_entities = zip(doc_orms, extracted_entities)
            if _logger.isEnabledFor(logging.INFO):
                docs_and_entities = tqdm(
                    docs_and_entities, desc="Extracting entities", total=len(docs)
                )
            for doc, doc_entities in docs_and_entities:
                doc_tuplets = self._cooccurrence_extractor.extract(doc, doc_entities)
                self._db_service.add_tuplets(doc, doc_tuplets)

            _logger.info("Resolving entities")
            tuplets = self._db_service.get_tuplets()
            entities = [
                entity
                for tuplet in tuplets
                for entity in [
                    tuplet.entity_one_span_text,
                    tuplet.entity_two_span_text,
                ]
            ]
            self.entity_mapping = self._entity_mapper.create_mapping(entities)

            _logger.info("Mapping tuplets")
            self._db_service.map_tuplets_only(self.entity_mapping)

            _logger.info("Calculating stats")
            n_docs = len(docs)
            self._db_service.update_entity_info_from_tuplets(n_docs=n_docs)
            self._db_service.update_cooccurrence_info(n_docs=n_docs)

            return self
