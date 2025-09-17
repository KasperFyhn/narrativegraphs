from typing import Optional

from fastapi import Depends, HTTPException, APIRouter
from sqlalchemy.orm import Session

from narrativegraph.db.orms import DocumentOrm
from narrativegraph.dto.documents import Document, transform_orm_to_dto
from narrativegraph.service import QueryService
from narrativegraph.server.routes.common import get_query_service

router = APIRouter()


def get_docs_by_ids(
    db: Session, doc_ids: list[int], limit: Optional[int] = None
) -> list[Document]:
    """Get multiple documents by IDs"""
    query = db.query(DocumentOrm).filter(DocumentOrm.id.in_(doc_ids))
    if limit:
        query = query.limit(limit)

    doc_orms = query.all()
    return [transform_orm_to_dto(doc_orm) for doc_orm in doc_orms]


@router.get("/{doc_id}", response_model=Document)
async def get_doc(
    doc_id: int,
    service: QueryService = Depends(get_query_service),
):
    """Get a single document by ID"""
    doc = service.docs.by_id(doc_id)
    if doc is None:
        raise HTTPException(status_code=404, detail="Could not find document!")
    return doc


@router.post("/", response_model=list[Document])
async def get_docs(
    doc_ids: list[int],
    limit: Optional[int] = None,
    service: QueryService = Depends(get_query_service),
):
    return service.docs.by_ids(doc_ids, limit=limit)
