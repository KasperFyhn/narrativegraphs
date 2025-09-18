import math
from datetime import date

from sqlalchemy import func
from sqlalchemy.orm import Session, InstrumentedAttribute
from tqdm import tqdm

from narrativegraph.db.common import TextOccurrenceMixin
from narrativegraph.db.documents import DocumentCategory, DocumentOrm
from narrativegraph.db.predicates import PredicateOrm, PredicateCategory
from narrativegraph.db.triplets import TripletOrm
from narrativegraph.db.relations import (
    RelationCategory,
    RelationOrm,
    CoOccurrenceOrm,
    CoOccurrenceCategory,
)
from narrativegraph.db.entities import EntityCategory, EntityOrm
from narrativegraph.nlp.extraction.common import Triplet
from narrativegraph.service.common import DbService


class PopulationService(DbService):

    def _bulk_save_with_categories(
        self,
        bulk: list[DocumentOrm],
        categories: list[dict[str, list[str]]],
    ) -> None:
        with self.get_session_context() as sc:
            sc.add_all(bulk)
            sc.flush()
            cat_bulk = []
            for item, cat_dict in zip(bulk, categories):
                for name, values in cat_dict.items():
                    for value in values:
                        cat_orm = DocumentCategory(
                            target_id=item.id,
                            name=name,
                            value=value,
                        )
                        cat_bulk.append(cat_orm)
                if len(cat_bulk) > 1000:
                    sc.bulk_save_objects(cat_bulk)
            # save any remaining in the bulk
            sc.bulk_save_objects(cat_bulk)
            sc.flush()

    def add_documents(
        self,
        docs: list[str],
        doc_ids: list[int | str] = None,
        timestamps: list[date] = None,
        categories: list[dict[str, list[str]]] = None,
    ):
        if doc_ids is None:
            doc_ids = [None] * len(docs)
        if timestamps is None:
            timestamps = [None] * len(docs)
        if categories is None:
            categories = [{}] * len(docs)

        assert (
            len(doc_ids) == len(timestamps) == len(categories) == len(docs)
        ), "Document metadata (ids, timestamps, categories) must be the same length as input documents"

        bulk = []
        doc_cats = []
        with self.get_session_context() as sc:
            for doc_text, doc_id, timestamp, categorization in zip(
                docs, doc_ids, timestamps, categories, strict=True
            ):
                doc_orm = DocumentOrm(
                    text=doc_text,
                    id=doc_id if isinstance(doc_id, int) else None,
                    str_id=doc_id if isinstance(doc_id, str) else None,
                    timestamp=timestamp,
                )
                bulk.append(doc_orm)
                doc_cats.append(categorization)

                if len(bulk) >= 500:
                    self._bulk_save_with_categories(bulk, doc_cats)
                    bulk.clear()
                    doc_cats.clear()

            # save any remaining in the bulk
            self._bulk_save_with_categories(bulk, doc_cats)

    def get_docs(
        self,
    ) -> list[DocumentOrm]:
        with self.get_session_context() as sc:
            return sc.query(DocumentOrm).all()

    def add_triplets(
        self,
        doc_id: int,
        triplets: list[Triplet],
    ):
        with self.get_session_context() as sc:
            triplet_orms = [
                TripletOrm(
                    doc_id=doc_id,
                    subj_span_start=triplet.subj.start_char,
                    subj_span_end=triplet.subj.end_char,
                    subj_span_text=triplet.subj.text,
                    pred_span_start=triplet.pred.start_char,
                    pred_span_end=triplet.pred.end_char,
                    pred_span_text=triplet.pred.text,
                    obj_span_start=triplet.obj.start_char,
                    obj_span_end=triplet.obj.end_char,
                    obj_span_text=triplet.obj.text,
                )
                for triplet in triplets
            ]
            sc.bulk_save_objects(triplet_orms)

    def map_triplets(
        self,
        entity_mappings: dict[str, str],
        predicate_mappings: dict[str, str],
    ):
        with self.get_session_context() as sc:
            cache = Cache(sc, entity_mappings, predicate_mappings)

            for triplet in tqdm(sc.query(TripletOrm).all(), desc="Mapping triplets"):
                subject_id = cache.get_or_create_entity(triplet.subj_span_text)
                predicate_id = cache.get_or_create_predicate(
                    triplet.pred_span_text,
                )
                object_id = cache.get_or_create_entity(triplet.obj_span_text)
                relation_id = cache.get_or_create_relation(
                    subject_id,
                    predicate_id,
                    object_id,
                )
                co_occurrence_id = cache.get_or_create_co_occurrence(
                    subject_id,
                    object_id,
                )

                triplet.subject_id = subject_id
                triplet.predicate_id = predicate_id
                triplet.object_id = object_id
                triplet.relation_id = relation_id
                triplet.co_occurrence_id = co_occurrence_id

            sc.commit()

            cache.calculate_stats()

    def get_triplets(
        self,
    ):
        with self.get_session_context() as sc:
            return sc.query(TripletOrm).all()


class Cache:

    def __init__(
        self,
        session: Session,
        entity_mappings: dict[str, str],
        predicate_mappings: dict[str, str],
    ):
        self._session = session
        self._entities = {str(e.label): e for e in session.query(EntityOrm).all()}
        self._predicates = {str(p.label): p for p in session.query(PredicateOrm).all()}
        self._relations = {
            (int(r.subject_id), int(r.predicate_id), int(r.object_id)): r  # noqa
            for r in session.query(RelationOrm).all()
        }
        self._co_occurrences = {
            (int(co.entity_one_id), int(co.entity_two_id)): co  # noqa
            for co in session.query(CoOccurrenceOrm).all()
        }

        self._entity_mappings = entity_mappings
        self._predicate_mappings = predicate_mappings

    def get_or_create_entity(self, label: InstrumentedAttribute[str] | str):
        """Fetch an entity by label, or create it if it doesn't exist."""
        mapped_entity = self._entity_mappings[label]

        entity = self._entities.get(mapped_entity, None)
        if entity is None:
            entity = EntityOrm(label=mapped_entity)
            self._session.add(entity)
            self._session.flush()  # Get the ID immediately
            self._entities[mapped_entity] = entity  # noqa
        return entity.id

    def get_or_create_predicate(
        self,
        label: InstrumentedAttribute[str] | str,
    ):
        """Fetch a predicate by label, or create it if it doesn't exist."""
        mapped_predicate = self._predicate_mappings[label]

        predicate = self._predicates.get(mapped_predicate, None)
        if predicate is None:
            predicate = PredicateOrm(
                label=mapped_predicate,
            )
            self._session.add(predicate)
            self._session.flush()  # Get the ID immediately
            self._predicates[mapped_predicate] = predicate  # noqa
        return predicate.id

    def get_or_create_relation(
        self, subject_id: int, predicate_id: int, object_id: int
    ):
        relation_key = (
            subject_id,
            predicate_id,
            object_id,
        )

        co_occurrence_id = self.get_or_create_co_occurrence(subject_id, object_id)

        relation = self._relations.get(relation_key, None)
        if relation is None:
            relation = RelationOrm(
                subject_id=subject_id,
                predicate_id=predicate_id,
                object_id=object_id,
                co_occurrence_id=co_occurrence_id,
            )
            self._session.add(relation)
            self._session.flush()  # Get the ID immediately
            self._relations[relation_key] = relation
        return relation.id

    def get_or_create_co_occurrence(
        self,
        entity_id_1: int,
        entity_id_2: int,
    ):
        if entity_id_1 < entity_id_2:
            key = entity_id_1, entity_id_2
        else:
            key = entity_id_2, entity_id_1
        co_occurrence = self._co_occurrences.get(key, None)
        if co_occurrence is None:
            co_occurrence = CoOccurrenceOrm(
                entity_one_id=entity_id_1,
                entity_two_id=entity_id_2,
            )
            self._session.add(co_occurrence)
            self._session.flush()  # Get the ID immediately
            self._co_occurrences[key] = co_occurrence
        return co_occurrence.id

    def update_entity_info(self, n_docs: int = None):
        if n_docs is None:
            n_docs = self._session.query(DocumentOrm).count()
        for entity in tqdm(self._entities.values(), desc="Updating entity info"):
            TextOccurrenceMixin.set_from_triplets(
                entity, entity.triplets, n_docs=n_docs
            )
            category_orms = EntityCategory.from_categorizable(
                entity.id, entity.triplets
            )
            self._session.add_all(category_orms)

        self._session.commit()

    def update_predicate_info(self, n_docs: int = None):
        if n_docs is None:
            n_docs = self._session.query(DocumentOrm).count()
        for predicate in tqdm(
            self._predicates.values(),
            desc="Updating predicate info",
        ):
            TextOccurrenceMixin.set_from_triplets(
                predicate, predicate.triplets, n_docs=n_docs
            )

            category_orms = PredicateCategory.from_categorizable(
                predicate.id, predicate.triplets
            )
            self._session.add_all(category_orms)

        self._session.commit()

    def update_relation_info(self, n_docs: int = None):
        if n_docs is None:
            n_docs = self._session.query(DocumentOrm).count()
        for relation in tqdm(
            self._relations.values(),
            desc="Updating relation info",
        ):
            TextOccurrenceMixin.set_from_triplets(
                relation, relation.triplets, n_docs=n_docs
            )

            category_orms = RelationCategory.from_categorizable(
                relation.id, relation.triplets
            )
            self._session.add_all(category_orms)

        self._session.commit()

    def update_co_occurrence_info(self, n_docs: int = None):
        if n_docs is None:
            n_docs = self._session.query(DocumentOrm).count()
        total_entity_occurrences = self._session.query(
            func.sum(EntityOrm.frequency)
        ).scalar()
        for co_occurrence in tqdm(
            self._co_occurrences.values(),
            desc="Updating co-occurrence info",
        ):
            TextOccurrenceMixin.set_from_triplets(
                co_occurrence, co_occurrence.triplets, n_docs=n_docs
            )

            co_occurrence.pmi = (
                math.log(co_occurrence.frequency)
                + math.log(total_entity_occurrences)
                - math.log(co_occurrence.entity_one.frequency)
                - math.log(co_occurrence.entity_two.frequency)
            )

            category_orms = CoOccurrenceCategory.from_categorizable(
                co_occurrence.id, co_occurrence.triplets
            )
            self._session.add_all(category_orms)

        self._session.commit()

    def calculate_stats(self):
        n_docs = self._session.query(DocumentOrm).count()

        self.update_entity_info(n_docs=n_docs)
        self.update_predicate_info()
        self.update_relation_info()
        self.update_co_occurrence_info()
