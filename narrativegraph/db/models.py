from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class Entity(BaseModel):
    id: int
    label: str
    term_frequency: Optional[int] = None
    doc_frequency: Optional[int] = None
    first_occurrence: Optional[datetime] = None
    last_occurrence: Optional[datetime] = None

    subject_triplets: list["TripletOrm"]
    object_triplets: list["TripletOrm"]


class Relation(BaseModel):
    __tablename__ = "relations"
    id = Column(Integer, primary_key=True, autoincrement=True)
    label = Column(String, nullable=False, index=True)
    subject_id = Column(Integer, ForeignKey("entities.id"), nullable=False, index=True)
    object_id = Column(Integer, ForeignKey("entities.id"), nullable=False, index=True)
    term_frequency = Column(Integer, default=-1, nullable=False)
    doc_frequency = Column(Integer, default=-1, nullable=False)
    first_occurrence = Column(DateTime, nullable=True)
    last_occurrence = Column(DateTime, nullable=True)

    # Relationships
    subject = relationship(
        "EntityOrm",
        foreign_keys="RelationOrm.subject_id",
    )
    object = relationship(
        "EntityOrm",
        foreign_keys="RelationOrm.object_id",
    )
    triplets: Mapped[list["TripletOrm"]] = relationship(
        "TripletOrm",
        back_populates="predicate",
        foreign_keys="TripletOrm.relation_id",
    )


class Triplet(BaseModel):
    id: int
    timestamp = Column(DateTime, nullable=True)
    doc_id = Column(Integer, ForeignKey("docs.id"), nullable=False, index=True)
    subject_id = Column(Integer, ForeignKey("entities.id"), nullable=True, index=True)
    relation_id = Column(Integer, ForeignKey("relations.id"), nullable=True, index=True)
    object_id = Column(Integer, ForeignKey("entities.id"), nullable=True, index=True)
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
        "RelationOrm",
        foreign_keys="TripletOrm.relation_id",
    )
    object = relationship(
        "EntityOrm",
        foreign_keys="TripletOrm.object_id",
    )
    document = relationship(
        "DocumentOrm",
        foreign_keys="TripletOrm.doc_id",
        back_populates="triplets",
    )

    __table_args__ = (UniqueConstraint(
        'doc_id',
        'subject_entity_id',
        'predicate_relation_id',
        'object_entity_id',
        name='unique_triplet_constraint'
    ),)


class Document(BaseModel):
    text: str
    id: Optional[int]
    str_id: Optional[str]
    timestamp: Optional[datetime] = None
