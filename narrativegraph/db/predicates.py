from sqlalchemy import Column, Integer, ForeignKey, String, Date
from sqlalchemy.orm import relationship, Mapped

from narrativegraph.db.common import CategoryMixin, CategorizableMixin, TextOccurrenceMixin
from narrativegraph.db.engine import Base
from narrativegraph.db.relations import RelationOrm
from narrativegraph.db.triplets import TripletOrm


class PredicateCategory(Base, CategoryMixin):
    __tablename__ = "predicates_categories"
    target_id = Column(Integer, ForeignKey("predicates.id"), nullable=False, index=True)


class PredicateOrm(Base, TextOccurrenceMixin, CategorizableMixin):
    __tablename__ = "predicates"
    id = Column(Integer, primary_key=True, autoincrement=True)
    label = Column(String, nullable=False, index=True)

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
