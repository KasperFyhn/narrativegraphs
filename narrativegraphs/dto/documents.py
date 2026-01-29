from datetime import date
from typing import Optional

from narrativegraphs.db.documents import DocumentOrm
from narrativegraphs.dto.common import BaseDetails
from narrativegraphs.dto.triplets import Triplet, Tuplet


class Document(BaseDetails):
    str_id: Optional[str] = None
    text: str
    timestamp: Optional[date]
    triplets: list[Triplet]
    tuplets: list[Tuplet]

    @classmethod
    def from_orm(cls, doc_orm: DocumentOrm) -> "Document":
        """Transform ORM model to DTO"""
        return cls(
            id=doc_orm.id,
            str_id=doc_orm.str_id,
            text=doc_orm.text,
            timestamp=doc_orm.timestamp,
            triplets=Triplet.from_orms(doc_orm.triplets),
            tuplets=Tuplet.from_orms(doc_orm.tuplets),
            categories=doc_orm.category_dict,
        )
