from sqlalchemy import Column, Integer, ForeignKey, String, Boolean, Date
from sqlalchemy.orm import relationship, Mapped

from narrativegraph.db.common import CategoryMixin, CategorizableMixin
from narrativegraph.db.engine import Base
from narrativegraph.db.triplets import TripletOrm


class EntityCategory(Base, CategoryMixin):
    __tablename__ = "entities_categories"
    target_id = Column(Integer, ForeignKey("entities.id"), nullable=False, index=True)


class EntityOrm(Base, CategorizableMixin):
    __tablename__ = "entities"
    id = Column(Integer, primary_key=True, autoincrement=True)
    label = Column(String, nullable=False, index=True)
    supernode_id = Column(Integer, ForeignKey("entities.id"), nullable=True, index=True)
    is_supernode = Column(Boolean, nullable=False, default=False)
    term_frequency = Column(Integer, default=-1, nullable=False)
    doc_frequency = Column(Integer, default=-1, nullable=False)
    first_occurrence = Column(Date, nullable=True)
    last_occurrence = Column(Date, nullable=True)

    # Relationships
    supernode = relationship(
        "EntityOrm",
        back_populates="subnodes",
        remote_side="EntityOrm.id",
        foreign_keys="EntityOrm.supernode_id",
    )
    subnodes = relationship("EntityOrm", back_populates="supernode")

    subject_triplets: Mapped[list["TripletOrm"]] = relationship(
        "TripletOrm",
        back_populates="subject",
        foreign_keys="TripletOrm.subject_id",
    )
    object_triplets: Mapped[list["TripletOrm"]] = relationship(
        "TripletOrm",
        back_populates="object",
        foreign_keys="TripletOrm.object_id",
    )

    categories: Mapped[list[EntityCategory]] = relationship(
        "EntityCategory",
        foreign_keys=[EntityCategory.target_id],
    )
