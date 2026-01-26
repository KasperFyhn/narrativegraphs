from sqlalchemy import (
    CheckConstraint,
    Column,
    Float,
    ForeignKey,
    Integer,
)
from sqlalchemy.orm import Mapped, relationship

from narrativegraphs.db.common import (
    CategorizableMixin,
    CategoryMixin,
)
from narrativegraphs.db.documents import AnnotationBackedTextStatsMixin
from narrativegraphs.db.engine import Base
from narrativegraphs.db.entities import EntityOrm
from narrativegraphs.db.tuplets import TupletOrm


class CooccurrenceCategory(Base, CategoryMixin):
    __tablename__ = "cooccurrences_categories"
    target_id = Column(
        Integer, ForeignKey("cooccurrences.id"), nullable=False, index=True
    )


class CooccurrenceOrm(Base, AnnotationBackedTextStatsMixin, CategorizableMixin):
    __tablename__ = "cooccurrences"
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
        foreign_keys="CooccurrenceOrm.entity_one_id",
    )
    entity_two: Mapped["EntityOrm"] = relationship(
        "EntityOrm",
        foreign_keys="CooccurrenceOrm.entity_two_id",
    )

    __table_args__ = (
        CheckConstraint("entity_one_id <= entity_two_id", name="entity_order_check"),
    )

    tuplets: Mapped[list["TupletOrm"]] = relationship(
        "TupletOrm",
        back_populates="cooccurrence",
        foreign_keys="TupletOrm.cooccurrence_id",
    )

    categories: Mapped[list[CooccurrenceCategory]] = relationship(
        "CooccurrenceCategory",
        foreign_keys="CooccurrenceCategory.target_id",
    )
