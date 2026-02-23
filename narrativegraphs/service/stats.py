from typing import Type

from sqlalchemy import Engine, func, insert, select, union_all, update
from sqlalchemy.orm import aliased
from sqlalchemy.orm.attributes import InstrumentedAttribute

from narrativegraphs.db.common import CategoryMixin
from narrativegraphs.db.cooccurrences import CooccurrenceCategory, CooccurrenceOrm
from narrativegraphs.db.documents import AnnotationMixin, DocumentCategory, DocumentOrm
from narrativegraphs.db.engine import Base
from narrativegraphs.db.entities import EntityCategory, EntityOrm
from narrativegraphs.db.entityoccurrences import EntityOccurrenceOrm
from narrativegraphs.db.predicates import PredicateCategory, PredicateOrm
from narrativegraphs.db.relations import RelationCategory, RelationOrm
from narrativegraphs.db.triplets import TripletOrm
from narrativegraphs.db.tuplets import TupletOrm
from narrativegraphs.service.common import DbService


class StatsCalculator(DbService):
    def __init__(self, engine: Engine, has_triplets: bool = True):
        super().__init__(engine)
        self.has_triplets = has_triplets

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
                        backing_annotation_type.doc_id.label("doc_id"),
                        backing_annotation_type.timestamp.label("timestamp"),
                        backing_annotation_type.timestamp_ordinal.label(
                            "timestamp_ordinal"
                        ),
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
                    func.min(annotation_union.c.timestamp_ordinal).label(
                        "first_occurrence_ordinal"
                    ),
                    func.max(annotation_union.c.timestamp_ordinal).label(
                        "last_occurrence_ordinal"
                    ),
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
                    first_occurrence_ordinal=stats_subquery.c.first_occurrence_ordinal,
                    last_occurrence_ordinal=stats_subquery.c.last_occurrence_ordinal,
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
                EntityOccurrenceOrm,
                EntityOccurrenceOrm.entity_id,
                n_docs,
            )
            self._update_categories_for_type(
                EntityCategory,
                EntityOccurrenceOrm,
                EntityOccurrenceOrm.entity_id,
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

    def _update_relation_significance(self):
        with self.get_session_context() as session:
            # Subquery to get entity pair frequencies (sum across all predicates)
            entity_pair_freq = (
                select(
                    RelationOrm.subject_id,
                    RelationOrm.object_id,
                    func.sum(RelationOrm.frequency).label("pair_frequency"),
                )
                .group_by(RelationOrm.subject_id, RelationOrm.object_id)
                .subquery()
            )

            # Calculate total corpus frequency N (sum of all predicate frequencies)
            total_corpus_freq = session.scalar(select(func.sum(PredicateOrm.frequency)))

            # Create subquery for significance calculation
            significance_subquery = (
                select(
                    RelationOrm.id,
                    (
                        # significance = P(predicate | entity1, entity2) / P(predicate)
                        # P(predicate | entity1, entity2) =
                        #       freq(relation) / freq(entity_pair)
                        # P(predicate) = freq(predicate) / N
                        # log(significance) =
                        #       log(freq(relation)) - log(freq(entity_pair))
                        #       - log(freq(predicate)) + log(N)
                        func.log(RelationOrm.frequency)
                        - func.log(entity_pair_freq.c.pair_frequency)
                        - func.log(PredicateOrm.frequency)
                        + func.log(total_corpus_freq)
                    ).label("significance"),
                )
                .join(
                    PredicateOrm,
                    RelationOrm.predicate_id == PredicateOrm.id,
                )
                .join(
                    entity_pair_freq,
                    (RelationOrm.subject_id == entity_pair_freq.c.subject_id)
                    & (RelationOrm.object_id == entity_pair_freq.c.object_id),
                )
                .subquery()
            )

            # Update RelationOrm with calculated significance
            significance_update = (
                update(RelationOrm)
                .values(significance=significance_subquery.c.significance)
                .where(RelationOrm.id == significance_subquery.c.id)
            )

            session.execute(significance_update)

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

            self._update_relation_significance()

            session.commit()

    def update_cooccurrence_info(self, n_docs: int = None):
        with self.get_session_context() as session:
            if n_docs is None:
                n_docs = session.query(DocumentOrm).count()

            # Stats
            self._update_stats_for_type(
                CooccurrenceOrm, TupletOrm, TupletOrm.cooccurrence_id, n_docs
            )

            # PMI calculation (special to co-occurrences)
            total_entity_occurrences = session.query(
                func.sum(EntityOrm.frequency)
            ).scalar()

            entity_one_alias = aliased(EntityOrm)
            entity_two_alias = aliased(EntityOrm)

            pmi_subquery = (
                select(
                    CooccurrenceOrm.id,
                    (
                        func.log(CooccurrenceOrm.frequency)
                        + func.log(total_entity_occurrences)
                        - func.log(entity_one_alias.frequency)
                        - func.log(entity_two_alias.frequency)
                    ).label("pmi"),
                )
                .join(
                    entity_one_alias,
                    CooccurrenceOrm.entity_one_id == entity_one_alias.id,
                )
                .join(
                    entity_two_alias,
                    CooccurrenceOrm.entity_two_id == entity_two_alias.id,
                )
                .subquery()
            )

            pmi_update = (
                update(CooccurrenceOrm)
                .values(pmi=pmi_subquery.c.pmi)
                .where(CooccurrenceOrm.id == pmi_subquery.c.id)
            )

            session.execute(pmi_update)

            self._update_categories_for_type(
                CooccurrenceCategory, TupletOrm, TupletOrm.cooccurrence_id
            )
            session.commit()

    def calculate_stats(self, has_triplets: bool = True):
        with self.get_session_context() as session:
            n_docs = session.query(DocumentOrm).count()

            self.update_entity_info(n_docs=n_docs)
            self.update_cooccurrence_info(n_docs=n_docs)
            if has_triplets:
                self.update_predicate_info(n_docs=n_docs)
                self.update_relation_info(n_docs=n_docs)
