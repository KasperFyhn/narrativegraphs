from sqlalchemy import Column, Date, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, relationship

from narrativegraphs.db.common import CategorizableMixin, CategoryMixin
from narrativegraphs.db.engine import Base


class DocumentCategory(Base, CategoryMixin):
    __tablename__ = "documents_categories"
    target_id = Column(Integer, ForeignKey("documents.id"), nullable=False, index=True)


class DocumentOrm(Base, CategorizableMixin):
    __tablename__ = "documents"
    id = Column(Integer, primary_key=True, autoincrement=True)
    text = Column(Text, nullable=False)

    str_id = Column(String, nullable=True, index=True)
    timestamp = Column(Date, nullable=True)

    # Relationships
    tuplets = relationship("TupletOrm", back_populates="document")
    triplets = relationship("TripletOrm", back_populates="document")

    categories: Mapped[list[DocumentCategory]] = relationship(
        "DocumentCategory", foreign_keys=[DocumentCategory.target_id]
    )


class AnnotationMixin(CategorizableMixin):
    doc_id = Column(Integer, ForeignKey("documents.id"), nullable=False, index=True)
    timestamp = Column(Date, nullable=True)

    document: DocumentOrm = None  # Should be overridden

    @property
    def categories(self) -> list[CategoryMixin]:
        return self.document.categories


class AnnotationBackedTextStatsMixin:
    frequency = Column(Integer, default=-1, nullable=False)
    doc_frequency = Column(Integer, default=-1, nullable=False)
    spread = Column(Float, default=-1, nullable=False)
    adjusted_tf_idf = Column(Float, default=-1, nullable=False)
    first_occurrence = Column(Date, nullable=True)
    last_occurrence = Column(Date, nullable=True)

    @classmethod
    def stats_columns(cls):
        return [
            cls.frequency,
            cls.doc_frequency,
            cls.spread,
            cls.adjusted_tf_idf,
            cls.first_occurrence,
            cls.last_occurrence,
        ]
