import logging
from datetime import date, datetime

from sqlalchemy import Engine
from tqdm import tqdm

from narrativegraphs.nlp.extraction import DependencyGraphExtractor, TripletExtractor
from narrativegraphs.nlp.extraction.cooccurrences import (
    ChunkCooccurrenceExtractor,
    CooccurrenceExtractor,
)
from narrativegraphs.nlp.mapping import Mapper
from narrativegraphs.nlp.mapping.linguistic import SubgramStemmingMapper
from narrativegraphs.service import PopulationService
from narrativegraphs.utils.transform import normalize_categories

logging.basicConfig(level=logging.INFO)
_logger = logging.getLogger("narrativegraphs.pipeline")
_logger.setLevel(logging.INFO)


class Pipeline:
    def __init__(
        self,
        engine: Engine,
        triplet_extractor: TripletExtractor = None,
        cooccurrence_extractor: CooccurrenceExtractor = None,
        entity_mapper: Mapper = None,
        predicate_mapper: Mapper = None,
        n_cpu: int = 1,
    ):
        # Analysis components
        self._triplet_extractor = triplet_extractor or DependencyGraphExtractor()
        self._cooccurrence_extractor = (
            cooccurrence_extractor or ChunkCooccurrenceExtractor()
        )
        self._entity_mapper = entity_mapper or SubgramStemmingMapper("noun")
        self._predicate_mapper = predicate_mapper or SubgramStemmingMapper("verb")

        self.n_cpu = n_cpu

        self._db_service = PopulationService(engine)
        self.predicate_mapping = None
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

            _logger.info("Extracting triplets")
            # TODO: use generators instead of lists here
            doc_orms = self._db_service.get_docs()
            extracted_triplets = self._triplet_extractor.batch_extract(
                [d.text for d in doc_orms], n_cpu=self.n_cpu
            )
            docs_and_triplets = zip(doc_orms, extracted_triplets)
            if _logger.isEnabledFor(logging.INFO):
                docs_and_triplets = tqdm(
                    docs_and_triplets, desc="Extracting triplets", total=len(docs)
                )
            for doc, doc_triplets in docs_and_triplets:
                self._db_service.add_triplets(
                    doc,
                    doc_triplets,
                )
                entities = list(
                    {e for triplet in doc_triplets for e in [triplet.subj, triplet.obj]}
                )
                doc_tuplets = self._cooccurrence_extractor.extract(doc, entities)
                self._db_service.add_tuplets(doc, doc_tuplets)

            _logger.info("Resolving entities and predicates")
            triplets = self._db_service.get_triplets()
            entities = [
                entity
                for triplet in triplets
                for entity in [triplet.subj_span_text, triplet.obj_span_text]
            ]
            self.entity_mapping = self._entity_mapper.create_mapping(entities)

            predicates = [triplet.pred_span_text for triplet in triplets]
            self.predicate_mapping = self._predicate_mapper.create_mapping(predicates)

            _logger.info("Mapping triplets and tuplets")
            self._db_service.map_triplets_and_tuplets(
                self.entity_mapping,
                self.predicate_mapping,
            )

            _logger.info("Calculating stats")
            self._db_service.calculate_stats()

            return self
