from datetime import date

from sqlalchemy import Column, Integer, ForeignKey, String
from sqlalchemy.orm import relationship

from narrativegraph.db.common import CategorizableMixin, CategoryMixin
from narrativegraph.db.engine import Base


class TripletOrm(Base, CategorizableMixin):
    __tablename__ = "triplets"
    id = Column(Integer, primary_key=True, autoincrement=True)
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
    def categories(self) -> list[CategoryMixin]:
        return self.document.categories

    @property
    def timestamp(self) -> date:
        return self.document.timestamp
