from datetime import date
from typing import Optional

from narrativegraphs.db.documents import DocumentOrm
from narrativegraphs.dto.common import BaseDetails, IdentifiableSpan
from narrativegraphs.dto.triplets import Triplet
from narrativegraphs.dto.tuplets import Tuplet


class Document(BaseDetails):
    str_id: Optional[str] = None
    text: str
    timestamp: Optional[date]
    triplets: Optional[list[Triplet]] = None
    tuplets: Optional[list[Tuplet]] = None
    entity_mentions: Optional[list[IdentifiableSpan]] = None

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
            entity_mentions=IdentifiableSpan.from_entity_occurrence_orms(
                doc_orm.entity_occurrences
            ),
            categories=doc_orm.category_dict,
        )
