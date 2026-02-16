import logging
from abc import ABC
from datetime import date, datetime

from sqlalchemy import Engine
from tqdm import tqdm

from narrativegraphs.nlp.common.transformcategories import normalize_categories
from narrativegraphs.nlp.entities.common import EntityExtractor
from narrativegraphs.nlp.entities.spacy import SpacyEntityExtractor
from narrativegraphs.nlp.mapping import Mapper
from narrativegraphs.nlp.mapping.linguistic import SubgramStemmingMapper
from narrativegraphs.nlp.triplets import DependencyGraphExtractor, TripletExtractor
from narrativegraphs.nlp.tuplets.common import CooccurrenceExtractor
from narrativegraphs.nlp.tuplets.cooccurrences import (
    ChunkCooccurrenceExtractor,
)
from narrativegraphs.service import PopulationService
from narrativegraphs.service.stats import StatsCalculator

logging.basicConfig(level=logging.INFO)
_logger = logging.getLogger("narrativegraphs.pipeline")
_logger.setLevel(logging.INFO)


class _AbstractPipeline(ABC):
    def __init__(
        self,
        engine: Engine,
        n_cpu: int = 1,
    ):
        self.n_cpu = n_cpu
        self._populator = PopulationService(engine)
        self._stats = StatsCalculator(engine)

    def _add_documents_to_db(
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
        with self._populator.get_session_context():
            _logger.info(f"Adding {len(docs)} documents to database")
            if categories is not None:
                categories = normalize_categories(categories)

            self._populator.add_documents(
                docs,
                doc_ids=doc_ids,
                timestamps=timestamps,
                categories=categories,
            )


class Pipeline(_AbstractPipeline):
    def __init__(
        self,
        engine: Engine,
        triplet_extractor: TripletExtractor = None,
        cooccurrence_extractor: CooccurrenceExtractor = None,
        entity_mapper: Mapper = None,
        predicate_mapper: Mapper = None,
        n_cpu: int = 1,
    ):
        super().__init__(engine, n_cpu=n_cpu)
        # Analysis components
        self._triplet_extractor = triplet_extractor or DependencyGraphExtractor()
        self._cooccurrence_extractor = (
            cooccurrence_extractor or ChunkCooccurrenceExtractor()
        )
        self._entity_mapper = entity_mapper or SubgramStemmingMapper("noun")
        self._predicate_mapper = predicate_mapper or SubgramStemmingMapper("verb")

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
        with self._populator.get_session_context():
            self._add_documents_to_db(docs, doc_ids, timestamps, categories)

            _logger.info("Extracting triplets")
            # TODO: use generators instead of lists here
            doc_orms = self._populator.get_docs()
            extracted_triplets = self._triplet_extractor.batch_extract(
                [d.text for d in doc_orms], n_cpu=self.n_cpu
            )
            docs_and_triplets = zip(doc_orms, extracted_triplets)
            if _logger.isEnabledFor(logging.INFO):
                docs_and_triplets = tqdm(
                    docs_and_triplets, desc="Extracting triplets", total=len(docs)
                )
            for doc, doc_triplets in docs_and_triplets:
                # Extract entities from triplets
                entities = list(
                    {e for triplet in doc_triplets for e in [triplet.subj, triplet.obj]}
                )
                # Add entity occurrences first, get lookup for efficient referencing
                occ_lookup = self._populator.add_entity_occurrences(doc, entities)
                # Then add triplets and tuplets that reference them
                self._populator.add_triplets(doc, doc_triplets, occ_lookup)
                doc_tuplets = self._cooccurrence_extractor.extract(doc, entities)
                self._populator.add_tuplets(doc, doc_tuplets, occ_lookup)

            _logger.info("Resolving entities and predicates")
            entities = [e.span_text for e in self._populator.get_entity_occurrences()]
            entity_mapping = self._entity_mapper.create_mapping(entities)

            predicates = [
                triplet.pred_span_text for triplet in self._populator.get_triplets()
            ]
            predicate_mapping = self._predicate_mapper.create_mapping(predicates)

            _logger.info("Mapping triplets and tuplets")
            self._populator.map_tuplets_and_triplets(
                entity_mapping,
                predicate_mapping,
            )

            _logger.info("Calculating stats")
            self._stats.calculate_stats()

            return self


class CooccurrencePipeline(_AbstractPipeline):
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
        super().__init__(engine, n_cpu)
        self._entity_extractor = entity_extractor or SpacyEntityExtractor()
        self._cooccurrence_extractor = (
            cooccurrence_extractor or ChunkCooccurrenceExtractor()
        )
        self._entity_mapper = entity_mapper or SubgramStemmingMapper("noun")

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
        with self._populator.get_session_context():
            _logger.info(f"Adding {len(docs)} documents to database")
            if categories is not None:
                categories = normalize_categories(categories)

            self._populator.add_documents(
                docs,
                doc_ids=doc_ids,
                timestamps=timestamps,
                categories=categories,
            )

            _logger.info("Extracting entities")
            doc_orms = self._populator.get_docs()
            extracted_entities = self._entity_extractor.batch_extract(
                [d.text for d in doc_orms], n_cpu=self.n_cpu
            )
            docs_and_entities = zip(doc_orms, extracted_entities)
            if _logger.isEnabledFor(logging.INFO):
                docs_and_entities = tqdm(
                    docs_and_entities, desc="Extracting entities", total=len(docs)
                )
            for doc, doc_entities in docs_and_entities:
                # Add entity occurrences first, get lookup for efficient referencing
                occ_lookup = self._populator.add_entity_occurrences(doc, doc_entities)
                # Then add tuplets that reference them
                doc_tuplets = self._cooccurrence_extractor.extract(doc, doc_entities)
                self._populator.add_tuplets(doc, doc_tuplets, occ_lookup)

            _logger.info("Resolving entities")
            entities = [e.span_text for e in self._populator.get_entity_occurrences()]
            entity_mapping = self._entity_mapper.create_mapping(entities)

            _logger.info("Mapping tuplets")
            self._populator.map_tuplets(entity_mapping)

            _logger.info("Calculating stats")
            self._stats.calculate_stats(has_triplets=False)

            return self
