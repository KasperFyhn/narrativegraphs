from sqlalchemy import Column, Date, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from narrativegraphs.db.documents import AnnotationMixin
from narrativegraphs.db.engine import Base


class TripletOrm(Base, AnnotationMixin):
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
    cooccurrence_id = Column(
        Integer, ForeignKey("cooccurrences.id"), nullable=True, index=True
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
    cooccurrence = relationship(
        "CooccurrenceOrm",
        foreign_keys="TripletOrm.cooccurrence_id",
    )
    document = relationship(
        "DocumentOrm",
        foreign_keys="TripletOrm.doc_id",
        back_populates="triplets",
    )
