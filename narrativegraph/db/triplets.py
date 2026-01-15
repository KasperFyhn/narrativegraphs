from sqlalchemy import Column, Date, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from narrativegraph.db.common import CategorizableMixin, CategoryMixin
from narrativegraph.db.engine import Base


class TripletOrm(Base, CategorizableMixin):
    __tablename__ = "triplets"
    id = Column(Integer, primary_key=True, autoincrement=True)
    doc_id = Column(Integer, ForeignKey("documents.id"), nullable=False, index=True)

    timestamp = Column(Date, nullable=True)

    subject_id = Column(Integer, ForeignKey("entities.id"), nullable=True, index=True)
    predicate_id = Column(
        Integer, ForeignKey("predicates.id"), nullable=True, index=True
    )
    object_id = Column(Integer, ForeignKey("entities.id"), nullable=True, index=True)
    relation_id = Column(Integer, ForeignKey("relations.id"), nullable=True, index=True)
    co_occurrence_id = Column(
        Integer, ForeignKey("co_occurrences.id"), nullable=True, index=True
    )

    subj_span_start = Column(Integer, nullable=False)
    subj_span_end = Column(Integer, nullable=False)
    subj_span_text = Column(String, nullable=False)
    pred_span_start = Column(Integer, nullable=False)
    pred_span_end = Column(Integer, nullable=False)
    pred_span_text = Column(String, nullable=False)
    obj_span_start = Column(Integer, nullable=False)
    obj_span_end = Column(Integer, nullable=False)
    obj_span_text = Column(String, nullable=False)

    # Relationships
    subject = relationship(
        "EntityOrm",
        foreign_keys="TripletOrm.subject_id",
    )
    predicate = relationship(
        "PredicateOrm",
        foreign_keys="TripletOrm.predicate_id",
    )
    object = relationship(
        "EntityOrm",
        foreign_keys="TripletOrm.object_id",
    )
    relation = relationship(
        "RelationOrm",
        foreign_keys="TripletOrm.relation_id",
    )
    co_occurrence = relationship(
        "CoOccurrenceOrm",
        foreign_keys="TripletOrm.co_occurrence_id",
    )
    document = relationship(
        "DocumentOrm",
        foreign_keys="TripletOrm.doc_id",
        back_populates="triplets",
    )

    @property
    def categories(self) -> list[CategoryMixin]:
        return self.document.categories


class TripletBackedTextStatsMixin:
    frequency = Column(Integer, default=-1, nullable=False)
    doc_frequency = Column(Integer, default=-1, nullable=False)
    adjusted_tf_idf = Column(Float, default=-1, nullable=False)
    first_occurrence = Column(Date, nullable=True)
    last_occurrence = Column(Date, nullable=True)

    @staticmethod
    def set_from_triplets(
        orm: "TripletBackedTextStatsMixin",
        triplets: list[TripletOrm],
        n_docs: int = None,
    ):
        orm.frequency = len(triplets)
        orm.doc_frequency = len(set(t.doc_id for t in triplets))
        if n_docs:
            orm.adjusted_tf_idf = (orm.frequency - 1) * (
                n_docs / (orm.doc_frequency + 1)
            )
        dates = [t.timestamp for t in triplets if t.timestamp is not None]
        orm.first_occurrence = min(dates, default=None)
        orm.last_occurrence = max(dates, default=None)

    @classmethod
    def stats_columns(cls):
        return [
            cls.frequency,
            cls.doc_frequency,
            cls.adjusted_tf_idf,
            cls.first_occurrence,
            cls.last_occurrence,
        ]
