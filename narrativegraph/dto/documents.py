from fastapi_camelcase import CamelModel

from narrativegraph.db.orms import DocumentOrm
from narrativegraph.dto.triplets import Triplet, SpanEntity


class Document(CamelModel):
    id: int
    text: str
    timestamp: str
    triplets: list[Triplet]
    categories: dict[str, list[str]]


def transform_orm_to_dto(doc_orm: DocumentOrm) -> Document:
    """Transform ORM model to DTO"""
    return Document(
        id=doc_orm.id,
        text=doc_orm.text,
        timestamp=doc_orm.timestamp.isoformat() if doc_orm.timestamp else "",
        triplets=[
            Triplet(
                subject=SpanEntity(
                    id=triplet_orm.subject_id,
                    start=triplet_orm.subj_span_start,
                    end=triplet_orm.subj_span_end,
                ),
                predicate=SpanEntity(
                    id=triplet_orm.relation_id,
                    start=triplet_orm.pred_span_start,
                    end=triplet_orm.pred_span_end,
                ),
                object=SpanEntity(
                    id=triplet_orm.object_id,
                    start=triplet_orm.obj_span_start,
                    end=triplet_orm.obj_span_end,
                ),
            )
            for triplet_orm in doc_orm.triplets
        ],
        categories=doc_orm.category_dict,
    )
