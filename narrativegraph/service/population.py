from datetime import date
from typing import Type

from sqlalchemy import func, insert, select, union_all, update
from sqlalchemy.orm import Session, aliased
from sqlalchemy.orm.attributes import InstrumentedAttribute

from narrativegraph.db.common import CategoryMixin
from narrativegraph.db.cooccurrences import CoOccurrenceCategory, CoOccurrenceOrm
from narrativegraph.db.documents import AnnotationMixin, DocumentCategory, DocumentOrm
from narrativegraph.db.engine import Base
from narrativegraph.db.entities import EntityCategory, EntityOrm
from narrativegraph.db.predicates import PredicateCategory, PredicateOrm
from narrativegraph.db.relations import (
    RelationCategory,
    RelationOrm,
)
from narrativegraph.db.triplets import (
    TripletOrm,
)
from narrativegraph.db.tuplets import TupletOrm
from narrativegraph.nlp.extraction.common import Triplet, Tuplet
from narrativegraph.service.common import DbService


class PopulationService(DbService):
    def _bulk_save_docs_with_categories(
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

        assert len(doc_ids) == len(timestamps) == len(categories) == len(docs), (
            "Document metadata (ids, timestamps, categories) must be the same "
            "length as input documents"
        )

        bulk = []
        doc_cats = []
        with self.get_session_context():
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
                    self._bulk_save_docs_with_categories(bulk, doc_cats)
                    bulk.clear()
                    doc_cats.clear()

            # save any remaining in the bulk
            self._bulk_save_docs_with_categories(bulk, doc_cats)

    def get_docs(
        self,
    ) -> list[DocumentOrm]:
        with self.get_session_context() as sc:
            return sc.query(DocumentOrm).all()

    def add_triplets(
        self,
        doc: DocumentOrm,
        triplets: list[Triplet],
    ):
        with self.get_session_context() as sc:
            triplet_orms = [
                TripletOrm(
                    doc_id=doc.id,
                    timestamp=doc.timestamp,
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

    def add_tuplets(
        self,
        doc: DocumentOrm,
        tuplets: list[Tuplet],
    ):
        with self.get_session_context() as sc:
            tuplet_orms = [
                TupletOrm(
                    doc_id=doc.id,
                    timestamp=doc.timestamp,
                    entity_one_span_start=tuplet.entity_one.start_char,
                    entity_one_span_end=tuplet.entity_one.end_char,
                    entity_one_span_text=tuplet.entity_one.text,
                    entity_two_span_start=tuplet.entity_two.start_char,
                    entity_two_span_end=tuplet.entity_two.end_char,
                    entity_two_span_text=tuplet.entity_two.text,
                )
                for tuplet in tuplets
            ]
            sc.bulk_save_objects(tuplet_orms)

    def map_triplets(
        self,
        entity_mappings: dict[str, str],
        predicate_mappings: dict[str, str],
    ):
        with self.get_session_context() as sc:
            triplets = self.get_triplets()
            tuplets = self.get_tuplets()

            cache = Cache(sc, entity_mappings, predicate_mappings, triplets, tuplets)

            for triplet in triplets:
                subject_id = cache.get_entity_id(triplet.subj_span_text)
                predicate_id = cache.get_predicate_id(
                    triplet.pred_span_text,
                )
                object_id = cache.get_entity_id(triplet.obj_span_text)
                relation_id = cache.get_relation_id(
                    subject_id,
                    predicate_id,
                    object_id,
                )
                co_occurrence_id = cache.get_co_occurrence_id(
                    subject_id,
                    object_id,
                )

                triplet.subject_id = subject_id
                triplet.predicate_id = predicate_id
                triplet.object_id = object_id
                triplet.relation_id = relation_id
                triplet.co_occurrence_id = co_occurrence_id

            for tuplet in tuplets:
                entity_one_id = cache.get_entity_id(tuplet.entity_one_span_text)
                entity_two_id = cache.get_entity_id(tuplet.entity_two_span_text)

                co_occurrence_id = cache.get_co_occurrence_id(
                    entity_one_id,
                    entity_two_id,
                )

                tuplet.entity_one_id = entity_one_id
                tuplet.entity_two_id = entity_two_id
                tuplet.co_occurrence_id = co_occurrence_id

            self.calculate_stats()

    def _update_stats_for_type(
        self,
        orm_class: Type[Base],
        backing_annotation_type: Type[AnnotationMixin],
        annotation_fk_columns: InstrumentedAttribute | list[InstrumentedAttribute],
        n_docs: int,
    ):
        """
        Generic stats update for any ORM type linked to annotations.

        Args:
            orm_class: The ORM class to update (EntityOrm, PredicateOrm, etc.)
            annotation_fk_columns: Single column or list of columns that link to this
                entity. If list, will UNION results (e.g., for entities as
                subject/object)
            n_docs: Total number of documents
        """

        # Normalize to list
        with self.get_session_context() as session:
            if not isinstance(annotation_fk_columns, list):
                annotation_fk_columns = [annotation_fk_columns]

            annotation_queries = []
            for fk_column in annotation_fk_columns:
                annotation_queries.append(
                    select(
                        fk_column.label("target_id"),
                        backing_annotation_type.id.label("annotation_id"),
                        backing_annotation_type.doc_id,
                        backing_annotation_type.timestamp,
                    ).where(fk_column.isnot(None))
                )

            # union_all handles single query case
            annotation_union = union_all(*annotation_queries).subquery()

            # Aggregate stats
            stats_subquery = (
                select(
                    annotation_union.c.target_id,
                    func.count(annotation_union.c.annotation_id).label("frequency"),
                    func.count(func.distinct(annotation_union.c.doc_id)).label(
                        "doc_frequency"
                    ),
                    func.min(annotation_union.c.timestamp).label("first_occurrence"),
                    func.max(annotation_union.c.timestamp).label("last_occurrence"),
                )
                .group_by(annotation_union.c.target_id)
                .subquery()
            )

            # Bulk update
            update_stmt = (
                update(orm_class)
                .values(
                    frequency=stats_subquery.c.frequency,
                    doc_frequency=stats_subquery.c.doc_frequency,
                    adjusted_tf_idf=(
                        (stats_subquery.c.frequency - 1)
                        * (n_docs / (stats_subquery.c.doc_frequency + 1))
                    ),
                    first_occurrence=stats_subquery.c.first_occurrence,
                    last_occurrence=stats_subquery.c.last_occurrence,
                )
                .where(orm_class.id == stats_subquery.c.target_id)
            )

            session.execute(update_stmt)

    def _update_categories_for_type(
        self,
        category_orm_class: Type[CategoryMixin],
        backing_annotation_type: Type[AnnotationMixin],
        annotation_fk_columns: InstrumentedAttribute | list[InstrumentedAttribute],
    ):
        """Generic category update for any type linked to annotations."""
        with self.get_session_context() as session:
            session.query(category_orm_class).delete()

            # Normalize to list
            if not isinstance(annotation_fk_columns, list):
                annotation_fk_columns = [annotation_fk_columns]

            # Build union of categories from all foreign key columns
            category_queries = []
            for fk_column in annotation_fk_columns:
                category_queries.append(
                    select(
                        fk_column.label("target_id"),
                        DocumentCategory.name,
                        DocumentCategory.value,
                    )
                    .join(DocumentOrm, backing_annotation_type.doc_id == DocumentOrm.id)
                    .join(
                        DocumentCategory, DocumentOrm.id == DocumentCategory.target_id
                    )
                    .where(fk_column.isnot(None))
                )

            # Build queries for all columns
            category_queries = []
            for fk_column in annotation_fk_columns:
                category_queries.append(
                    select(
                        fk_column.label("target_id"),
                        DocumentCategory.name,
                        DocumentCategory.value,
                    )
                    .join(DocumentOrm, backing_annotation_type.doc_id == DocumentOrm.id)
                    .join(
                        DocumentCategory, DocumentOrm.id == DocumentCategory.target_id
                    )
                    .where(fk_column.isnot(None))
                )
            categories_select = union_all(*category_queries).subquery()

            # Bulk insert
            insert_stmt = insert(category_orm_class).from_select(
                ["target_id", "name", "value"], categories_select
            )

            session.execute(insert_stmt)

    def update_entity_info(self, n_docs: int = None):
        with self.get_session_context() as session:
            if n_docs is None:
                n_docs = session.query(DocumentOrm).count()

            self._update_stats_for_type(
                EntityOrm,
                TripletOrm,
                [TripletOrm.subject_id, TripletOrm.object_id],
                n_docs,
            )
            self._update_categories_for_type(
                EntityCategory,
                TripletOrm,
                [TripletOrm.subject_id, TripletOrm.object_id],
            )
            session.commit()

    def update_predicate_info(self, n_docs: int = None):
        with self.get_session_context() as session:
            if n_docs is None:
                n_docs = session.query(DocumentOrm).count()

            self._update_stats_for_type(
                PredicateOrm, TripletOrm, TripletOrm.predicate_id, n_docs
            )
            self._update_categories_for_type(
                PredicateCategory, TripletOrm, TripletOrm.predicate_id
            )
            session.commit()

    def update_relation_info(self, n_docs: int = None):
        with self.get_session_context() as session:
            if n_docs is None:
                n_docs = session.query(DocumentOrm).count()

            self._update_stats_for_type(
                RelationOrm, TripletOrm, TripletOrm.relation_id, n_docs
            )
            self._update_categories_for_type(
                RelationCategory, TripletOrm, TripletOrm.relation_id
            )
            session.commit()

    def update_co_occurrence_info(self, n_docs: int = None):
        with self.get_session_context() as session:
            if n_docs is None:
                n_docs = session.query(DocumentOrm).count()

            # Stats
            self._update_stats_for_type(
                CoOccurrenceOrm, TupletOrm, TupletOrm.co_occurrence_id, n_docs
            )

            # PMI calculation (special to co-occurrences)
            total_entity_occurrences = session.query(
                func.sum(EntityOrm.frequency)
            ).scalar()

            entity_one_alias = aliased(EntityOrm)
            entity_two_alias = aliased(EntityOrm)

            pmi_subquery = (
                select(
                    CoOccurrenceOrm.id,
                    (
                        func.log(CoOccurrenceOrm.frequency)
                        + func.log(total_entity_occurrences)
                        - func.log(entity_one_alias.frequency)
                        - func.log(entity_two_alias.frequency)
                    ).label("pmi"),
                )
                .join(
                    entity_one_alias,
                    CoOccurrenceOrm.entity_one_id == entity_one_alias.id,
                )
                .join(
                    entity_two_alias,
                    CoOccurrenceOrm.entity_two_id == entity_two_alias.id,
                )
                .subquery()
            )

            pmi_update = (
                update(CoOccurrenceOrm)
                .values(pmi=pmi_subquery.c.pmi)
                .where(CoOccurrenceOrm.id == pmi_subquery.c.id)
            )

            session.execute(pmi_update)

            self._update_categories_for_type(
                CoOccurrenceCategory, TripletOrm, TripletOrm.co_occurrence_id
            )
            session.commit()

    def calculate_stats(self):
        with self.get_session_context() as session:
            n_docs = session.query(DocumentOrm).count()

            self.update_entity_info(n_docs=n_docs)
            self.update_predicate_info(n_docs=n_docs)
            self.update_relation_info(n_docs=n_docs)
            self.update_co_occurrence_info(n_docs=n_docs)

    def get_triplets(
        self,
    ):
        with self.get_session_context() as sc:
            return sc.query(TripletOrm).all()

    def get_tuplets(
        self,
    ):
        with self.get_session_context() as sc:
            return sc.query(TupletOrm).all()


class Cache:
    def __init__(
        self,
        session: Session,
        entity_mappings: dict[str, str],
        predicate_mappings: dict[str, str],
        triplets: list[TripletOrm],
        tuplets: list[TupletOrm],
    ):
        self._session = session
        self._entity_mappings = entity_mappings
        self._predicate_mappings = predicate_mappings

        self._entities = self._initialize_entities()
        self._predicates = self._initialize_predicates()

        self._co_occurrences = self._initialize_co_occurrences(tuplets)
        self._relations = self._initialize_relations(triplets)

    def _initialize_entities(self) -> dict[str, EntityOrm]:
        entities = {str(e.label): e for e in self._session.query(EntityOrm).all()}

        new_entities = []
        for mapped_entity in self._entity_mappings.values():
            if mapped_entity not in entities:
                new_entity = EntityOrm(label=mapped_entity)
                entities[mapped_entity] = new_entity
                new_entities.append(new_entity)

        if new_entities:
            self._session.add_all(new_entities)
            self._session.flush()  # Get IDs without committing

        return entities

    def _initialize_predicates(self) -> dict[str, PredicateOrm]:
        predicates = {str(p.label): p for p in self._session.query(PredicateOrm).all()}

        new_predicates = []
        for mapped_predicate in self._predicate_mappings.values():
            if mapped_predicate not in predicates:
                new_predicate = PredicateOrm(label=mapped_predicate)
                predicates[mapped_predicate] = new_predicate
                new_predicates.append(new_predicate)

        if new_predicates:
            self._session.add_all(new_predicates)
            self._session.flush()

        return predicates

    def _initialize_co_occurrences(
        self, tuplets: list[TupletOrm]
    ) -> dict[tuple[int, int], CoOccurrenceOrm]:
        co_occurrences = {
            (int(coc.entity_one_id), int(coc.entity_two_id)): coc
            for coc in self._session.query(CoOccurrenceOrm).all()
        }

        new_co_occurrences = []
        for triplet in tuplets:
            entity_id_1 = self.get_entity_id(triplet.entity_one_span_text)
            entity_id_2 = self.get_entity_id(triplet.entity_two_span_text)
            if entity_id_1 < entity_id_2:
                key = entity_id_1, entity_id_2
            else:
                key = entity_id_2, entity_id_1
            if key not in co_occurrences:
                co_occurrence = CoOccurrenceOrm(
                    entity_one_id=entity_id_1,
                    entity_two_id=entity_id_2,
                )
                co_occurrences[key] = co_occurrence
                new_co_occurrences.append(co_occurrence)

        if new_co_occurrences:
            self._session.add_all(new_co_occurrences)
            self._session.flush()

        return co_occurrences

    def _initialize_relations(
        self, triplets: list[TripletOrm]
    ) -> dict[tuple[int, int, int], RelationOrm]:
        relations = {
            (int(r.subject_id), int(r.predicate_id), int(r.object_id)): r
            for r in self._session.query(RelationOrm).all()
        }

        new_relations = []
        for triplet in triplets:
            subject_id = self.get_entity_id(triplet.subj_span_text)
            predicate_id = self.get_predicate_id(
                triplet.pred_span_text,
            )
            object_id = self.get_entity_id(triplet.obj_span_text)
            relation_key = (subject_id, predicate_id, object_id)
            if relation_key not in relations:
                coc_id = self.get_co_occurrence_id(subject_id, object_id)
                relation = RelationOrm(
                    subject_id=subject_id,
                    predicate_id=predicate_id,
                    object_id=object_id,
                    co_occurrence_id=coc_id,
                )
                relations[relation_key] = relation
                new_relations.append(relation)

        if new_relations:
            self._session.add_all(new_relations)
            self._session.flush()

        return relations

    def get_entity_id(self, label: InstrumentedAttribute[str] | str) -> int:
        """Fetch an entity by label, or create it if it doesn't exist."""
        mapped_entity = self._entity_mappings[label]

        entity = self._entities.get(mapped_entity, None)
        if entity is None:
            entity = EntityOrm(label=mapped_entity)
            self._session.add(entity)
            self._session.flush()  # Get the ID immediately
            self._entities[mapped_entity] = entity
        return entity.id

    def get_predicate_id(
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
            self._predicates[mapped_predicate] = predicate
        return predicate.id

    def get_relation_id(self, subject_id: int, predicate_id: int, object_id: int):
        relation_key = (
            subject_id,
            predicate_id,
            object_id,
        )

        co_occurrence_id = self.get_co_occurrence_id(subject_id, object_id)

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

    def get_co_occurrence_id(
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
