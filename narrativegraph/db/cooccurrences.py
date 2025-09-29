from sqlalchemy import Column, Integer, ForeignKey, Float
from sqlalchemy.orm import Mapped, relationship

from narrativegraph.db.common import CategoryMixin, CategorizableMixin
from narrativegraph.db.engine import Base
from narrativegraph.db.entities import EntityOrm
from narrativegraph.db.relations import RelationOrm
from narrativegraph.db.triplets import TripletOrm, TripletBackedTextStatsMixin


class CoOccurrenceCategory(Base, CategoryMixin):
    __tablename__ = "co_occurrences_categories"
    target_id = Column(
        Integer, ForeignKey("co_occurrences.id"), nullable=False, index=True
    )


class CoOccurrenceOrm(Base, TripletBackedTextStatsMixin, CategorizableMixin):
    __tablename__ = "co_occurrences"
    id = Column(Integer, primary_key=True, autoincrement=True)
    entity_one_id = Column(
        Integer, ForeignKey("entities.id"), nullable=False, index=True
    )
    entity_two_id = Column(
        Integer, ForeignKey("entities.id"), nullable=False, index=True
    )

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
