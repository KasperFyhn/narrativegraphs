from typing import Optional, Any

from fastapi import Depends, HTTPException, APIRouter
from sqlalchemy.orm import Session

from narrativegraph.db.orms import DocumentOrm
from narrativegraph.db.dtos import transform_orm_to_dto, Document
from narrativegraph.server.routes.common import get_db_session


router = APIRouter()

def get_docs_by_ids(db: Session, doc_ids: list[int], limit: Optional[int] = None) -> list[Document]:
    """Get multiple documents by IDs"""
    query = db.query(DocumentOrm).filter(DocumentOrm.id.in_(doc_ids))
    if limit:
        query = query.limit(limit)

    doc_orms = query.all()
    return [transform_orm_to_dto(doc_orm) for doc_orm in doc_orms]


@router.get("/{doc_id}", response_model=Document)
async def get_doc(doc_id: int, db: Session = Depends(get_db_session)):
    """Get a single document by ID"""
    doc_orm = db.query(DocumentOrm).filter(DocumentOrm.id == doc_id).first()

    if doc_orm is None:
        raise HTTPException(status_code=404, detail="Could not find document!")
    doc = transform_orm_to_dto(doc_orm)
    return doc


@router.post("/", response_model=list[Document])
async def get_docs(doc_request: Any, limit: Optional[int] = None,
                   db: Session = Depends(get_db_session)):
    """Get multiple documents by IDs"""
    doc_ids = doc_request.doc_ids
    return get_docs_by_ids(db, doc_ids, limit)
