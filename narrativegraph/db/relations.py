from typing import TYPE_CHECKING

from sqlalchemy import Column, ForeignKey, Integer, func, select
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import Mapped, relationship

from narrativegraph.db.common import (
    CategorizableMixin,
    CategoryMixin,
    HasAltLabels,
)
from narrativegraph.db.documents import AnnotationBackedTextStatsMixin
from narrativegraph.db.engine import Base
from narrativegraph.db.entities import EntityOrm
from narrativegraph.db.predicates import PredicateOrm
from narrativegraph.db.triplets import TripletOrm

if TYPE_CHECKING:
    pass


class RelationCategory(Base, CategoryMixin):
    __tablename__ = "relations_categories"
    target_id = Column(Integer, ForeignKey("relations.id"), nullable=False, index=True)


class RelationOrm(
    Base, AnnotationBackedTextStatsMixin, CategorizableMixin, HasAltLabels
):
    __tablename__ = "relations"
    id = Column(Integer, primary_key=True, autoincrement=True)
    subject_id = Column(Integer, ForeignKey("entities.id"), nullable=False, index=True)
    predicate_id = Column(
        Integer, ForeignKey("predicates.id"), nullable=False, index=True
    )
    object_id = Column(Integer, ForeignKey("entities.id"), nullable=False, index=True)

    @property
    def label(self) -> str:
        return self.predicate.label

    @hybrid_property
    def alt_labels(self) -> list[str]:
        """Python version"""
        return list(set(triplet.pred_span_text for triplet in self.triplets))

    @alt_labels.expression
    def alt_labels(self):
        """SQL version - returns comma-separated string that pandas can split"""
        return (
            select(func.json_group_array(TripletOrm.pred_span_text.distinct()))
            .select_from(TripletOrm)
            .where(TripletOrm.relation_id == self.id)
            .scalar_subquery()
        )

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

    categories: Mapped[list[RelationCategory]] = relationship(
        "RelationCategory", foreign_keys=[RelationCategory.target_id]
    )
