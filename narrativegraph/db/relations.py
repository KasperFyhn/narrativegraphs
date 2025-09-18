from sqlalchemy import Column, Integer, ForeignKey, Date, Float
from sqlalchemy.orm import relationship, Mapped

from narrativegraph.db.common import (
    CategoryMixin,
    CategorizableMixin,
    TextOccurrenceMixin,
)
from narrativegraph.db.engine import Base
from narrativegraph.db.entities import EntityOrm
from narrativegraph.db.triplets import TripletOrm


class RelationCategory(Base, CategoryMixin):
    __tablename__ = "relations_categories"
    target_id = Column(Integer, ForeignKey("relations.id"), nullable=False, index=True)


class RelationOrm(Base, TextOccurrenceMixin, CategorizableMixin):
    __tablename__ = "relations"
    id = Column(Integer, primary_key=True, autoincrement=True)
    subject_id = Column(Integer, ForeignKey("entities.id"), nullable=False, index=True)
    predicate_id = Column(Integer, ForeignKey("predicates.id"), nullable=False, index=True)
    object_id = Column(Integer, ForeignKey("entities.id"), nullable=False, index=True)
    co_occurrence_id = Column(Integer, ForeignKey("co_occurrences.id"), nullable=False, index=True)

    # Relationships
    subject: Mapped["EntityOrm"] = relationship(
        "EntityOrm",
        foreign_keys="RelationOrm.subject_id",
    )
    predicate: Mapped["PredicateOrm"] = relationship(
        "PredicateOrm",
        foreign_keys="RelationOrm.predicate_id",
    )
    object: Mapped["EntityOrm"] = relationship(
        "EntityOrm",
        foreign_keys="RelationOrm.object_id",
    )
    triplets: Mapped[list["TripletOrm"]] = relationship(
        "TripletOrm",
        back_populates="relation",
        foreign_keys="TripletOrm.relation_id",
    )
    co_occurrence: Mapped["CoOccurrenceOrm"] = relationship(
        "CoOccurrenceOrm",
        back_populates="relations",
        foreign_keys="RelationOrm.co_occurrence_id",
    )

    categories: Mapped[list[RelationCategory]] = relationship(
        "RelationCategory", foreign_keys=[RelationCategory.target_id]
    )


class CoOccurrenceCategory(Base, CategoryMixin):
    __tablename__ = "co_occurrence_categories"
    target_id = Column(Integer, ForeignKey("co_occurrences.id"), nullable=False, index=True)


class CoOccurrenceOrm(Base, TextOccurrenceMixin, CategorizableMixin):
    __tablename__ = "co_occurrences"
    id = Column(Integer, primary_key=True, autoincrement=True)
    entity_one_id = Column(Integer, ForeignKey("entities.id"), nullable=False, index=True)
    entity_two_id = Column(Integer, ForeignKey("entities.id"), nullable=False, index=True)

    pmi = Column(Float, default=-1, nullable=False)

    entity_one: Mapped["EntityOrm"] = relationship(
        "EntityOrm",
        foreign_keys="CoOccurrenceOrm.entity_one_id",
    )
    entity_two: Mapped["EntityOrm"] = relationship(
        "EntityOrm",
        foreign_keys="CoOccurrenceOrm.entity_two_id",
    )

    relations: Mapped[list[RelationOrm]] = relationship(
        "RelationOrm",
        back_populates="co_occurrence",
        foreign_keys="RelationOrm.co_occurrence_id",
    )
    triplets: Mapped[list["TripletOrm"]] = relationship(
        "TripletOrm",
        back_populates="co_occurrence",
        foreign_keys="TripletOrm.co_occurrence_id",
    )

    categories: Mapped[list[CoOccurrenceCategory]] = relationship(
        "CoOccurrenceCategory",
        foreign_keys="CoOccurrenceCategory.target_id",
    )
