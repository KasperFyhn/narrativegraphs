from typing import TYPE_CHECKING

from sqlalchemy import Column, Integer, ForeignKey, String, select, func
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relationship, Mapped

from narrativegraph.db.common import (
    CategoryMixin,
    CategorizableMixin,
    HasAltLabels,
)
from narrativegraph.db.engine import Base
from narrativegraph.db.triplets import TripletOrm, TripletBackedTextStatsMixin

if TYPE_CHECKING:
    from narrativegraph.db.relations import RelationOrm


class PredicateCategory(Base, CategoryMixin):
    __tablename__ = "predicates_categories"
    target_id = Column(Integer, ForeignKey("predicates.id"), nullable=False, index=True)


class PredicateOrm(Base, TripletBackedTextStatsMixin, CategorizableMixin, HasAltLabels):
    __tablename__ = "predicates"
    id = Column(Integer, primary_key=True, autoincrement=True)
    label: str = Column(String, nullable=False, index=True)

    @hybrid_property
    def alt_labels(self) -> list[str]:
        """Python version"""
        return list(set(triplet.pred_span_text for triplet in self.triplets))

    @alt_labels.expression
    def alt_labels(cls):  # noqa
        """SQL version - returns comma-separated string that pandas can split"""
        return (
            select(func.json_group_array(TripletOrm.pred_span_text.distinct()))
            .select_from(TripletOrm)
            .where(TripletOrm.predicate_id == cls.id)
            .scalar_subquery()
        )

    triplets: Mapped[list["TripletOrm"]] = relationship(
        "TripletOrm",
        back_populates="predicate",
        foreign_keys="TripletOrm.predicate_id",
    )
    relations: Mapped[list["RelationOrm"]] = relationship(
        "RelationOrm",
        back_populates="predicate",
        foreign_keys="RelationOrm.predicate_id",
    )

    categories: Mapped[list[PredicateCategory]] = relationship(
        "PredicateCategory", foreign_keys=[PredicateCategory.target_id]
    )
