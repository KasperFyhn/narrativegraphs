from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, relationship

from narrativegraphs.db.documents import AnnotationMixin, DocumentOrm
from narrativegraphs.db.engine import Base


class EntityOccurrenceOrm(Base, AnnotationMixin):
    __tablename__ = "entity_occurrences"
    id = Column(Integer, primary_key=True, autoincrement=True)
    entity_id = Column(Integer, ForeignKey("entities.id"), nullable=True, index=True)

    span_start = Column(Integer, nullable=False)
    span_end = Column(Integer, nullable=False)
    span_text = Column(String, nullable=False, index=True)
    is_coref_resolved = Column(
        Boolean, nullable=False, default=False, server_default="0"
    )

    # Relationships
    entity = relationship(
        "EntityOrm",
        back_populates="occurrences",
        foreign_keys=[entity_id],
    )
    document: Mapped["DocumentOrm"] = relationship(
        "DocumentOrm",
        foreign_keys="EntityOccurrenceOrm.doc_id",
    )
