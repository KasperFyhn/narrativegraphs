from sqlalchemy import (
    Column,
    ForeignKey,
    Integer,
    String,
    func,
    select,
)
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import Mapped, relationship

from narrativegraphs.db.common import (
    CategorizableMixin,
    CategoryMixin,
    HasAltLabels,
)
from narrativegraphs.db.documents import AnnotationBackedTextStatsMixin
from narrativegraphs.db.engine import Base
from narrativegraphs.db.entityoccurrences import EntityOccurrenceOrm
from narrativegraphs.db.triplets import TripletOrm
from narrativegraphs.db.tuplets import TupletOrm


class EntityCategory(Base, CategoryMixin):
    __tablename__ = "entities_categories"
    target_id = Column(Integer, ForeignKey("entities.id"), nullable=False, index=True)


class EntityOrm(Base, HasAltLabels, AnnotationBackedTextStatsMixin, CategorizableMixin):
    __tablename__ = "entities"
    id = Column(Integer, primary_key=True, autoincrement=True)
    label: str = Column(String, nullable=False, index=True)

    @hybrid_property
    def alt_labels(self) -> list[str]:
        return list(
            {occ.span_text for occ in self.occurrences if occ.span_text != self.label}
        )

    @alt_labels.expression
    def alt_labels(cls):  # noqa
        return (
            select(func.json_group_array(EntityOccurrenceOrm.span_text.distinct()))
            .where(EntityOccurrenceOrm.entity_id == cls.id)
            .where(EntityOccurrenceOrm.span_text != cls.label)
            .scalar_subquery()
        )

    # Entity occurrences relationship (unified source for all entity mentions)
    occurrences: Mapped[list["EntityOccurrenceOrm"]] = relationship(
        "EntityOccurrenceOrm",
        back_populates="entity",
        foreign_keys="EntityOccurrenceOrm.entity_id",
    )

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

    _entity_one_tuplets: Mapped[list["TupletOrm"]] = relationship(
        "TupletOrm",
        back_populates="entity_one",
        foreign_keys="TupletOrm.entity_one_id",
    )
    _entity_two_tuplets: Mapped[list["TupletOrm"]] = relationship(
        "TupletOrm",
        back_populates="entity_two",
        foreign_keys="TupletOrm.entity_two_id",
    )

    @property
    def tuplets(self):
        return self._entity_one_tuplets + self._entity_two_tuplets

    @property
    def _annotations(self):
        return self.triplets + self.tuplets

    subject_relations = relationship(
        "RelationOrm", back_populates="subject", foreign_keys="RelationOrm.subject_id"
    )
    object_relations = relationship(
        "RelationOrm", back_populates="object", foreign_keys="RelationOrm.object_id"
    )

    @property
    def relations(self):
        return self.subject_relations + self.object_relations

    _entity_one_cooccurrences = relationship(
        "CooccurrenceOrm",
        back_populates="entity_one",
        foreign_keys="CooccurrenceOrm.entity_one_id",
    )
    _entity_two_cooccurrences = relationship(
        "CooccurrenceOrm",
        back_populates="entity_two",
        foreign_keys="CooccurrenceOrm.entity_two_id",
    )

    @property
    def cooccurrences(self):
        return self._entity_one_cooccurrences + self._entity_two_cooccurrences
