from sqlalchemy import Column, Integer, ForeignKey, String, Boolean, Date
from sqlalchemy.orm import relationship, Mapped

from narrativegraph.db.common import CategoryMixin, CategorizableMixin, TextOccurrenceMixin
from narrativegraph.db.engine import Base
from narrativegraph.db.triplets import TripletOrm


class EntityCategory(Base, CategoryMixin):
    __tablename__ = "entities_categories"
    target_id = Column(Integer, ForeignKey("entities.id"), nullable=False, index=True)


class EntityOrm(Base, TextOccurrenceMixin, CategorizableMixin):
    __tablename__ = "entities"
    id = Column(Integer, primary_key=True, autoincrement=True)
    label = Column(String, nullable=False, index=True)

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

    @property
    def triplets(self):
        return self.subject_triplets + self.object_triplets

    categories: Mapped[list[EntityCategory]] = relationship(
        "EntityCategory",
        foreign_keys=[EntityCategory.target_id],
    )

    subject_relations = relationship(
        "RelationOrm",
        back_populates="subject",
        foreign_keys="RelationOrm.subject_id"
    )
    object_relations = relationship(
        "RelationOrm",
        back_populates="object",
        foreign_keys="RelationOrm.object_id"
    )
    @property
    def relations(self):
        return self.subject_relations + self.object_relations

    _entity_one_co_occurrences = relationship(
        "CoOccurrenceOrm",
        back_populates="entity_one",
        foreign_keys="CoOccurrenceOrm.entity_one_id",
    )
    _entity_two_co_occurrences = relationship(
        "CoOccurrenceOrm",
        back_populates="entity_two",
        foreign_keys="CoOccurrenceOrm.entity_two_id",
    )
    @property
    def co_occurrences(self):
        return self._entity_one_co_occurrences + self._entity_two_co_occurrences
