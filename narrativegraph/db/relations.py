from sqlalchemy import Column, Integer, ForeignKey, Date, String
from sqlalchemy.orm import relationship, Mapped

from narrativegraph.db.common import CategoryMixin, CategorizableMixin
from narrativegraph.db.engine import Base
from narrativegraph.db.entities import EntityOrm
from narrativegraph.db.triplets import TripletOrm


class RelationCategory(Base, CategoryMixin):
    __tablename__ = "relations_categories"
    target_id = Column(Integer, ForeignKey("relations.id"), nullable=False, index=True)


class RelationOrm(Base, CategorizableMixin):
    __tablename__ = "relations"
    id = Column(Integer, primary_key=True, autoincrement=True)
    subject_id = Column(Integer, ForeignKey("entities.id"), nullable=False, index=True)
    predicate_id = Column(Integer, ForeignKey("predicates.id"), nullable=False, index=True)
    object_id = Column(Integer, ForeignKey("entities.id"), nullable=False, index=True)
    term_frequency = Column(Integer, default=-1, nullable=False)
    doc_frequency = Column(Integer, default=-1, nullable=False)
    first_occurrence = Column(Date, nullable=True)
    last_occurrence = Column(Date, nullable=True)

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
