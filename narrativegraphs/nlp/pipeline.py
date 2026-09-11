import logging
from abc import ABC, abstractmethod
from datetime import date, datetime
from typing import Any

from sqlalchemy import Engine
from tqdm.auto import tqdm

from narrativegraphs.nlp.common.annotation import SpanAnnotation
from narrativegraphs.nlp.common.mentions import expand_to_all_occurrences
from narrativegraphs.nlp.common.transformcategories import normalize_categories
from narrativegraphs.nlp.entities.common import EntityExtractor
from narrativegraphs.nlp.entities.spacy import SpacyEntityExtractor
from narrativegraphs.nlp.mapping import Mapper
from narrativegraphs.nlp.mapping.linguistic import (
    SubgramLemmatizationMapper,
)
from narrativegraphs.nlp.triplets import DependencyGraphExtractor, TripletExtractor
from narrativegraphs.nlp.triplets.common import Triplet
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
        timestamps_ordinal: list[int] = None,
        categories: (
            list[str | list[str]]
            | dict[str, list[str | list[str]]]
            | list[dict[str, str | list[str]]]
        ) = None,
        metadata: list[dict[str, Any]] = None,
    ):
        with self._populator.get_session_context():
            _logger.info(f"Adding {len(docs)} documents to database")
            if categories is not None:
                categories = normalize_categories(categories)

            self._populator.add_documents(
                docs,
                doc_ids=doc_ids,
                timestamps=timestamps,
                timestamps_ordinal=timestamps_ordinal,
                categories=categories,
                metadata=metadata,
            )

    @abstractmethod
    def _process_docs(self, annotations: list[list[Any]] = None):
        pass

    def run(
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
        metadata: list[dict[str, Any]] = None,
        annotations: list[list[Any]] = None,
    ):
        """Add documents to the database and build the graph from them.

        Args:
            docs: the documents as strings
            doc_ids: optional document ids, same length as docs
            timestamps: optional document timestamps, same length as docs
            timestamps_ordinal: optional integer timestamps, same length as docs
            categories: optional document categories
            metadata: optional document metadata, same length as docs
            annotations: optional pre-computed annotations, one list per
                document, which are used instead of running the extractor.
                Lets extraction be done once — or elsewhere, as with a batch
                run collected the next day — and reused across several fits.
        """
        if annotations is not None and len(annotations) != len(docs):
            raise ValueError(
                f"Got {len(annotations)} annotation lists for {len(docs)} documents; "
                "there must be exactly one list per document, in the same order."
            )
        self._add_documents_to_db(
            docs, doc_ids, timestamps, timestamps_ordinal, categories, metadata
        )
        self._process_docs(annotations)


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
        """Initialize the pipeline.

        Args:
            engine: SQLAlchemy engine for database access.
            triplet_extractor: Extractor for subject-predicate-object triplets
                (default: DependencyGraphExtractor).
            cooccurrence_extractor: Extractor for entity co-occurrences
                (default: ChunkCooccurrenceExtractor).
            entity_mapper: Mapper for entity normalization
                (default: SubgramLemmatizationMapper("noun")).
            predicate_mapper: Mapper for predicate normalization
                (default: SubgramLemmatizationMapper("verb")).
            n_cpu: Number of CPUs for parallel processing.
        """
        super().__init__(engine, n_cpu=n_cpu)
        # Analysis components
        self._triplet_extractor = triplet_extractor or DependencyGraphExtractor()
        self._cooccurrence_extractor = (
            cooccurrence_extractor or ChunkCooccurrenceExtractor()
        )
        self._entity_mapper = entity_mapper or SubgramLemmatizationMapper("noun")
        self._predicate_mapper = predicate_mapper or SubgramLemmatizationMapper("verb")

    def _process_docs(self, annotations: list[list[Triplet]] = None):
        with self._populator.get_session_context():
            # TODO: use generators instead of lists here
            doc_orms = self._populator.get_docs()
            if annotations is not None:
                _logger.info("Using pre-computed triplets")
                extracted_triplets = enumerate(annotations)
            else:
                _logger.info("Extracting triplets")
                # Keyed by index rather than zipped, so that extractors which
                # finish documents out of order are stored as results land.
                extracted_triplets = self._triplet_extractor.batch_extract_unordered(
                    [d.text for d in doc_orms], n_cpu=self.n_cpu
                )
            if _logger.isEnabledFor(logging.INFO):
                extracted_triplets = tqdm(
                    extracted_triplets,
                    desc="Extracting triplets",
                    total=len(doc_orms),
                )
            for doc_index, doc_triplets in extracted_triplets:
                doc = doc_orms[doc_index]
                # Extract entities from the triplets, then record every
                # other mention of them the document makes: extractors only
                # report the entities of the relations they found, and a
                # generative model consolidates a relation stated several
                # times into one.
                entities = list(
                    {e for triplet in doc_triplets for e in [triplet.subj, triplet.obj]}
                )
                entities = expand_to_all_occurrences(doc.text, entities)
                # Add entity occurrences first, get lookup for efficient referencing
                occ_lookup = self._populator.add_entity_occurrences(doc, entities)
                # Then add triplets and tuplets that reference them
                self._populator.add_triplets(doc, doc_triplets, occ_lookup)
                doc_tuplets = self._cooccurrence_extractor.extract(doc, entities)
                self._populator.add_tuplets(doc, doc_tuplets, occ_lookup)

            _logger.info("Resolving entities and predicates")
            occurrences = self._populator.get_entity_occurrences()
            entities = [e.span_text for e in occurrences if not e.is_coref_resolved]
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
                (default: SubgramLemmatizationMapper)
            n_cpu: Number of CPUs for parallel processing
        """
        super().__init__(engine, n_cpu)
        self._entity_extractor = entity_extractor or SpacyEntityExtractor()
        self._cooccurrence_extractor = (
            cooccurrence_extractor or ChunkCooccurrenceExtractor()
        )
        self._entity_mapper = entity_mapper or SubgramLemmatizationMapper("noun")

    def _process_docs(self, annotations: list[list[SpanAnnotation]] = None):
        with self._populator.get_session_context():
            doc_orms = self._populator.get_docs()
            if annotations is not None:
                _logger.info("Using pre-computed entities")
                extracted_entities = iter(annotations)
            else:
                _logger.info("Extracting entities")
                extracted_entities = self._entity_extractor.batch_extract(
                    [d.text for d in doc_orms], n_cpu=self.n_cpu
                )
            docs_and_entities = zip(doc_orms, extracted_entities)
            if _logger.isEnabledFor(logging.INFO):
                docs_and_entities = tqdm(
                    docs_and_entities, desc="Extracting entities", total=len(doc_orms)
                )
            for doc, doc_entities in docs_and_entities:
                # Add entity occurrences first, get lookup for efficient referencing
                occ_lookup = self._populator.add_entity_occurrences(doc, doc_entities)
                # Then add tuplets that reference them
                doc_tuplets = self._cooccurrence_extractor.extract(doc, doc_entities)
                self._populator.add_tuplets(doc, doc_tuplets, occ_lookup)

            _logger.info("Resolving entities")
            occurrences = self._populator.get_entity_occurrences()
            entities = [e.span_text for e in occurrences if not e.is_coref_resolved]
            entity_mapping = self._entity_mapper.create_mapping(entities)

            _logger.info("Mapping tuplets")
            self._populator.map_tuplets(entity_mapping)

            _logger.info("Calculating stats")
            self._stats.calculate_stats(has_triplets=False)
