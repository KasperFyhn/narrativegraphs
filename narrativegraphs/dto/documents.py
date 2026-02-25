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
    timestamp_ordinal: Optional[int]
    triplets: Optional[list[Triplet]] = None
    tuplets: Optional[list[Tuplet]] = None
    entity_mentions: Optional[list[IdentifiableSpan]] = None
    metadata: Optional[dict[str, str]] = None

    @classmethod
    def from_orm(
        cls,
        doc_orm: DocumentOrm,
        include_triplets: bool = False,
        include_tuplets: bool = False,
        include_mentions: bool = False,
    ) -> "Document":
        """Transform ORM model to DTO with optional relation loading"""
        return cls(
            id=doc_orm.id,
            str_id=doc_orm.str_id,
            text=doc_orm.text,
            timestamp=doc_orm.timestamp,
            timestamp_ordinal=doc_orm.timestamp_ordinal,
            triplets=Triplet.from_orms(doc_orm.triplets) if include_triplets else None,
            tuplets=Tuplet.from_orms(doc_orm.tuplets) if include_tuplets else None,
            entity_mentions=(
                IdentifiableSpan.from_entity_occurrence_orms(doc_orm.entity_occurrences)
                if include_mentions
                else None
            ),
            categories=doc_orm.category_dict,
            metadata=doc_orm.meta_dict,
        )
