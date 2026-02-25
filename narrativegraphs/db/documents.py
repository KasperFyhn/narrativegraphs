from typing import Optional

from sqlalchemy import Column, Date, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, relationship

from narrativegraphs.db.common import CategorizableMixin, CategoryMixin
from narrativegraphs.db.engine import Base


class DocumentMetadata(Base):
    __tablename__ = "document_metadata"
    name = Column(String)
    value = Column(String)
    doc_id = Column(Integer, ForeignKey("documents.id"))


class DocumentCategory(Base, CategoryMixin):
    __tablename__ = "documents_categories"
    target_id = Column(Integer, ForeignKey("documents.id"), nullable=False, index=True)


class DocumentOrm(Base, CategorizableMixin):
    __tablename__ = "documents"
    id = Column(Integer, primary_key=True, autoincrement=True)
    text = Column(Text, nullable=False)

    str_id = Column(String, nullable=True, index=True)
    timestamp = Column(Date, nullable=True)
    timestamp_ordinal = Column(Integer, nullable=True)

    # Relationships
    entity_occurrences = relationship("EntityOccurrenceOrm", back_populates="document")
    tuplets = relationship("TupletOrm", back_populates="document")
    triplets = relationship("TripletOrm", back_populates="document")

    categories: Mapped[list[DocumentCategory]] = relationship(
        "DocumentCategory", foreign_keys=[DocumentCategory.target_id]
    )

    meta: Mapped[list[DocumentMetadata]] = relationship(
        "DocumentMetadata", foreign_keys=[DocumentMetadata.doc_id]
    )

    @property
    def meta_dict(self) -> Optional[dict[str, str]]:
        result = {m.name: m.value for m in self.meta}
        if not result:
            return None
        return result


class AnnotationMixin(CategorizableMixin):
    doc_id = Column(Integer, ForeignKey("documents.id"), nullable=False, index=True)
    context = Column(Text, nullable=True)
    context_offset = Column(Integer, nullable=True)
    document: DocumentOrm = None  # Should be overridden

    @property
    def timestamp(self):
        return self.document.timestamp

    @property
    def timestamp_ordinal(self):
        return self.document.timestamp_ordinal

    @property
    def categories(self) -> list[CategoryMixin]:
        return self.document.categories


class AnnotationBackedTextStatsMixin:
    frequency = Column(Integer, default=-1, nullable=False)
    doc_frequency = Column(Integer, default=-1, nullable=False)
    adjusted_tf_idf = Column(Float, default=-1, nullable=False)
    first_occurrence = Column(Date, nullable=True)
    last_occurrence = Column(Date, nullable=True)
    first_occurrence_ordinal = Column(Integer, nullable=True)
    last_occurrence_ordinal = Column(Integer, nullable=True)

    @classmethod
    def stats_columns(cls):
        return [
            cls.frequency,
            cls.doc_frequency,
            cls.adjusted_tf_idf,
            cls.first_occurrence,
            cls.last_occurrence,
            cls.first_occurrence_ordinal,
            cls.last_occurrence_ordinal,
        ]

    @property
    def _annotations(self):
        """Return the annotations (triplets/tuplets) backing this ORM."""
        raise NotImplementedError("Subclass must implement _annotations")

    @property
    def doc_ids(self) -> set[int]:
        """Return the set of document IDs where this item occurs."""
        return {ann.doc_id for ann in self._annotations}
