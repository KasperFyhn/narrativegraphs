from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from narrativegraphs.db.documents import AnnotationMixin
from narrativegraphs.db.engine import Base


class TupletOrm(Base, AnnotationMixin):
    __tablename__ = "tuplets"
    id = Column(Integer, primary_key=True, autoincrement=True)

    entity_one_id = Column(
        Integer, ForeignKey("entities.id"), nullable=True, index=True
    )
    entity_two_id = Column(
        Integer, ForeignKey("entities.id"), nullable=True, index=True
    )
    cooccurrence_id = Column(
        Integer, ForeignKey("cooccurrences.id"), nullable=True, index=True
    )

    entity_one_span_start = Column(Integer, nullable=False)
    entity_one_span_end = Column(Integer, nullable=False)
    entity_one_span_text = Column(String, nullable=False)
    entity_two_span_start = Column(Integer, nullable=False)
    entity_two_span_end = Column(Integer, nullable=False)
    entity_two_span_text = Column(String, nullable=False)

    # Relationships
    entity_one = relationship(
        "EntityOrm",
        foreign_keys="TupletOrm.entity_one_id",
    )

    entity_two = relationship(
        "EntityOrm",
        foreign_keys="TupletOrm.entity_two_id",
    )

    cooccurrence = relationship(
        "CooccurrenceOrm",
        foreign_keys="TupletOrm.cooccurrence_id",
    )
    document = relationship(
        "DocumentOrm",
        foreign_keys="TupletOrm.doc_id",
        back_populates="tuplets",
    )
