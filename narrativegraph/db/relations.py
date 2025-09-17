from sqlalchemy import Column, Integer, ForeignKey, String, Date
from sqlalchemy.orm import relationship, Mapped

from narrativegraph.db.common import CategoryMixin, CategorizableMixin
from narrativegraph.db.engine import Base
from narrativegraph.db.triplets import TripletOrm


class RelationCategory(Base, CategoryMixin):
    __tablename__ = "relations_categories"
    target_id = Column(Integer, ForeignKey("relations.id"), nullable=False, index=True)


class RelationOrm(Base, CategorizableMixin):
    __tablename__ = "relations"
    id = Column(Integer, primary_key=True, autoincrement=True)
    label = Column(String, nullable=False, index=True)
    subject_id = Column(Integer, ForeignKey("entities.id"), nullable=False, index=True)
    object_id = Column(Integer, ForeignKey("entities.id"), nullable=False, index=True)
    term_frequency = Column(Integer, default=-1, nullable=False)
    doc_frequency = Column(Integer, default=-1, nullable=False)
    first_occurrence = Column(Date, nullable=True)
    last_occurrence = Column(Date, nullable=True)

    # Relationships
    subject = relationship(
        "EntityOrm",
        foreign_keys="RelationOrm.subject_id",
    )
    object = relationship(
        "EntityOrm",
        foreign_keys="RelationOrm.object_id",
    )
    triplets: Mapped[list["TripletOrm"]] = relationship(
        "TripletOrm",
        back_populates="predicate",
        foreign_keys="TripletOrm.relation_id",
    )

    categories: Mapped[list[RelationCategory]] = relationship(
        "RelationCategory", foreign_keys=[RelationCategory.target_id]
    )
