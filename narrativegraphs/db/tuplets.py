from sqlalchemy import Column, ForeignKey, Integer
from sqlalchemy.orm import Mapped, relationship

from narrativegraphs.db.documents import AnnotationMixin, DocumentOrm
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

    entity_one_occurrence_id = Column(
        Integer, ForeignKey("entity_occurrences.id"), nullable=False, index=True
    )
    entity_two_occurrence_id = Column(
        Integer, ForeignKey("entity_occurrences.id"), nullable=False, index=True
    )

    # Relationships
    entity_one = relationship(
        "EntityOrm",
        foreign_keys="TupletOrm.entity_one_id",
        back_populates="_entity_one_tuplets",
    )

    entity_two = relationship(
        "EntityOrm",
        foreign_keys="TupletOrm.entity_two_id",
        back_populates="_entity_two_tuplets",
    )

    cooccurrence = relationship(
        "CooccurrenceOrm",
        foreign_keys="TupletOrm.cooccurrence_id",
    )
    document: Mapped["DocumentOrm"] = relationship(
        "DocumentOrm",
        foreign_keys="TupletOrm.doc_id",
        back_populates="tuplets",
    )
    entity_one_occurrence = relationship(
        "EntityOccurrenceOrm",
        foreign_keys="TupletOrm.entity_one_occurrence_id",
    )
    entity_two_occurrence = relationship(
        "EntityOccurrenceOrm",
        foreign_keys="TupletOrm.entity_two_occurrence_id",
    )
