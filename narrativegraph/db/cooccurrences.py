from sqlalchemy import (
    CheckConstraint,
    Column,
    Float,
    ForeignKey,
    Integer,
)
from sqlalchemy.orm import Mapped, relationship

from narrativegraph.db.common import (
    CategorizableMixin,
    CategoryMixin,
)
from narrativegraph.db.documents import AnnotationBackedTextStatsMixin
from narrativegraph.db.engine import Base
from narrativegraph.db.entities import EntityOrm
from narrativegraph.db.tuplets import TupletOrm


class CoOccurrenceCategory(Base, CategoryMixin):
    __tablename__ = "co_occurrences_categories"
    target_id = Column(
        Integer, ForeignKey("co_occurrences.id"), nullable=False, index=True
    )


class CoOccurrenceOrm(Base, AnnotationBackedTextStatsMixin, CategorizableMixin):
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

    __table_args__ = (
        CheckConstraint("entity_one_id <= entity_two_id", name="entity_order_check"),
    )

    tuplets: Mapped[list["TupletOrm"]] = relationship(
        "TupletOrm",
        back_populates="co_occurrence",
        foreign_keys="TupletOrm.co_occurrence_id",
    )

    categories: Mapped[list[CoOccurrenceCategory]] = relationship(
        "CoOccurrenceCategory",
        foreign_keys="CoOccurrenceCategory.target_id",
    )
