import logging
from datetime import datetime, date

from tqdm import tqdm

from narrativegraph.service import PopulationService
from narrativegraph.nlp.extraction import TripletExtractor
from narrativegraph.nlp.extraction import DependencyGraphExtractor
from narrativegraph.nlp.mapping import Mapper
from narrativegraph.nlp.mapping.linguistic import StemmingMapper, SubgramStemmingMapper
from narrativegraph.utils.transform import normalize_categories

logging.basicConfig(level=logging.INFO)
_logger = logging.getLogger("narrativegraph.pipeline")
_logger.setLevel(logging.INFO)


class Pipeline:
    def __init__(
        self,
        triplet_extractor: TripletExtractor = None,
        entity_mapper: Mapper = None,
        relation_mapper: Mapper = None,
        sqlite_db_path: str = None,
    ):
        # Analysis components
        self._triplet_extractor = triplet_extractor or DependencyGraphExtractor()
        self._entity_mapper = entity_mapper or StemmingMapper()
        self._relation_mapper = relation_mapper or SubgramStemmingMapper()

        self._db_service = PopulationService(sqlite_db_path)

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
            self._db_service.add_documents(
                docs,
                doc_ids=doc_ids,
                timestamps=timestamps,
                categories=normalize_categories(categories),
                
            )

            _logger.info("Extracting triplets")
            doc_orms = self._db_service.get_docs()
            extracted_triplets = self._triplet_extractor.batch_extract(
                [d.text for d in doc_orms]
            )
            docs_and_triplets = zip(doc_orms, extracted_triplets)
            if _logger.isEnabledFor(logging.INFO):
                docs_and_triplets = tqdm(
                    docs_and_triplets, desc="Extracting triplets", total=len(docs)
                )
            for doc, doc_triplets in docs_and_triplets:
                self._db_service.add_triplets(doc.id, doc_triplets, )

            _logger.info("Mapping entities and relations")
            triplets = self._db_service.get_triplets()
            entities = [
                entity
                for triplet in triplets
                for entity in [triplet.subj_span_text, triplet.obj_span_text]
            ]
            self.entity_mapping = self._entity_mapper.create_mapping(entities)

            predicates = [triplet.pred_span_text for triplet in triplets]
            self.predicate_mapping = self._entity_mapper.create_mapping(predicates)

            _logger.info("Mapping triplets")
            self._db_service.map_triplets(
                self.entity_mapping, self.predicate_mapping, 
            )

            return self
