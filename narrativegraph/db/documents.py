from datetime import date

from sqlalchemy import Column, Date, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, relationship

from narrativegraph.db.common import CategorizableMixin, CategoryMixin
from narrativegraph.db.engine import Base
from narrativegraph.db.triplets import TripletOrm


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
    triplets: Mapped[list[TripletOrm]] = relationship(
        "TripletOrm", back_populates="document"
    )

    categories: Mapped[list[DocumentCategory]] = relationship(
        "DocumentCategory", foreign_keys=[DocumentCategory.target_id]
    )


class DocumentAnchoredAnnotationMixin:
    doc_id = Column(Integer, ForeignKey("documents.id"), nullable=False, index=True)

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
