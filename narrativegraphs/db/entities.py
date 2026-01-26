from sqlalchemy import (
    Column,
    ForeignKey,
    Integer,
    String,
    case,
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
from narrativegraphs.db.triplets import TripletOrm


class EntityCategory(Base, CategoryMixin):
    __tablename__ = "entities_categories"
    target_id = Column(Integer, ForeignKey("entities.id"), nullable=False, index=True)


class EntityOrm(Base, HasAltLabels, AnnotationBackedTextStatsMixin, CategorizableMixin):
    __tablename__ = "entities"
    id = Column(Integer, primary_key=True, autoincrement=True)
    label: str = Column(String, nullable=False, index=True)

    @hybrid_property
    def alt_labels(self) -> list[str]:
        subj_labels = [
            triplet.subj_span_text
            for triplet in self.subject_triplets
            if triplet.subj_span_text != self.label
        ]
        obj_labels = [
            triplet.obj_span_text
            for triplet in self.object_triplets
            if triplet.obj_span_text != self.label
        ]
        return list(set(subj_labels + obj_labels))

    @alt_labels.expression
    def alt_labels(cls):  # noqa
        return (
            select(
                func.json_group_array(
                    case(
                        (TripletOrm.subject_id == cls.id, TripletOrm.subj_span_text),
                        (TripletOrm.object_id == cls.id, TripletOrm.obj_span_text),
                    ).distinct()
                )
            )
            .select_from(TripletOrm)
            .where((TripletOrm.subject_id == cls.id) | (TripletOrm.object_id == cls.id))
            .scalar_subquery()
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
