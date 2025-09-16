from collections import defaultdict

from sqlalchemy import (
    Column,
    Integer,
    String,
    ForeignKey,
    Text,
    Boolean,
    Date,
)
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import declarative_base, relationship, Mapped

Base = declarative_base()


def combine_category_dicts(*dicts: dict[str, list[str]]) -> dict[str, list[str]]:
    result = defaultdict(set)
    for d in dicts:
        for name, values in d.items():
            result[name].update(values)
    return {name: list(values) for name, values in result.items()}


class CategoryMixin:
    id = Column(Integer, primary_key=True)
    target_id = Column(Integer, index=True)
    name = Column(String)
    value = Column(String)

    @classmethod
    def from_triplets(
        cls, item_id, triplets: list["TripletOrm"]
    ) -> list["CategoryMixin"]:
        categories = combine_category_dicts(*[t.category_dict for t in triplets])
        return [
            cls(
                target_id=item_id,  # noqa
                name=cat_name,  # noqa
                value=cat_value,  # noqa
            )
            for cat_name, cat_values in categories.items()
            for cat_value in cat_values
        ]


class CategorizableMixin:
    categories: Mapped[list[CategoryMixin]]

    @hybrid_property
    def category_dict(self) -> dict[str, list[str]]:
        result = defaultdict(set)
        for cat in self.categories:
            result[cat.name].add(cat.value)
        return {name: list(values) for name, values in result.items()}


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


class DocumentCategory(Base, CategoryMixin):
    __tablename__ = "documents_categories"
    target_id = Column(Integer, ForeignKey("documents.id"), nullable=False, index=True)


class TripletOrm(Base, CategorizableMixin):
    __tablename__ = "triplets"
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(Date, nullable=True)
    category = Column(String, nullable=True, index=True)
    doc_id = Column(Integer, ForeignKey("documents.id"), nullable=False, index=True)

    subject_id = Column(Integer, ForeignKey("entities.id"), nullable=True, index=True)
    relation_id = Column(Integer, ForeignKey("relations.id"), nullable=True, index=True)
    object_id = Column(Integer, ForeignKey("entities.id"), nullable=True, index=True)

    subj_span_start = Column(Integer, nullable=False)
    subj_span_end = Column(Integer, nullable=False)
    subj_span_text = Column(String, nullable=False)
    pred_span_start = Column(Integer, nullable=False)
    pred_span_end = Column(Integer, nullable=False)
    pred_span_text = Column(String, nullable=False)
    obj_span_start = Column(Integer, nullable=False)
    obj_span_end = Column(Integer, nullable=False)
    obj_span_text = Column(String, nullable=False)

    # Relationships
    subject = relationship(
        "EntityOrm",
        foreign_keys="TripletOrm.subject_id",
    )
    predicate = relationship(
        "RelationOrm",
        foreign_keys="TripletOrm.relation_id",
    )
    object = relationship(
        "EntityOrm",
        foreign_keys="TripletOrm.object_id",
    )
    document = relationship(
        "DocumentOrm",
        foreign_keys="TripletOrm.doc_id",
        back_populates="triplets",
    )

    @property
    def categories(self) -> list[DocumentCategory]:
        return self.document.categories


class DocumentOrm(Base, CategorizableMixin):
    __tablename__ = "documents"
    id = Column(Integer, primary_key=True, autoincrement=True)
    text = Column(Text, nullable=False)

    str_id = Column(String, nullable=True, index=True)
    timestamp = Column(Date, nullable=True)
    category = Column(String, nullable=True)

    # Relationships
    triplets: Mapped[list[TripletOrm]] = relationship(
        "TripletOrm", back_populates="document"
    )

    categories: Mapped[list[DocumentCategory]] = relationship(
        "DocumentCategory", foreign_keys=[DocumentCategory.target_id]
    )
