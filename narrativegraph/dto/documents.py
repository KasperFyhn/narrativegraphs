from datetime import date
from typing import Optional

from narrativegraph.db.documents import DocumentOrm
from narrativegraph.dto.common import BaseDetails
from narrativegraph.dto.triplets import Triplet


class Document(BaseDetails):
    text: str
    timestamp: Optional[date]
    triplets: list[Triplet]

    @classmethod
    def from_orm(cls, doc_orm: DocumentOrm) -> "Document":
        """Transform ORM model to DTO"""
        return cls(
            id=doc_orm.id,
            text=doc_orm.text,
            timestamp=doc_orm.timestamp,
            triplets=Triplet.from_orms(doc_orm.triplets),
            categories=doc_orm.category_dict,
        )
