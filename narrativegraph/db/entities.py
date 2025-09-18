from sqlalchemy import (
    Column,
    Integer,
    ForeignKey,
    String,
    Boolean,
    Date,
    select,
    func,
    case,
)
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relationship, Mapped

from narrativegraph.db.common import (
    CategoryMixin,
    CategorizableMixin,
    TextStatsMixin,
    HasAltLabels,
)
from narrativegraph.db.engine import Base
from narrativegraph.db.triplets import TripletOrm


class EntityCategory(Base, CategoryMixin):
    __tablename__ = "entities_categories"
    target_id = Column(Integer, ForeignKey("entities.id"), nullable=False, index=True)


class EntityOrm(Base, HasAltLabels, TextStatsMixin, CategorizableMixin):
    __tablename__ = "entities"
    id = Column(Integer, primary_key=True, autoincrement=True)
    label: str = Column(String, nullable=False, index=True)

    @hybrid_property
    def alt_labels(self) -> list[str]:
        subj_labels = [triplet.subj_span_text for triplet in self.subject_triplets]
        obj_labels = [triplet.obj_span_text for triplet in self.object_triplets]
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
