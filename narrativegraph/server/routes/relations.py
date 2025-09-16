from typing import Optional

from fastapi import Depends, HTTPException, APIRouter
from sqlalchemy.orm import Session

from narrativegraph.db.orms import DocumentOrm, TripletOrm, RelationOrm
from narrativegraph.db.dtos import transform_relation_orm_to_details, Details
from narrativegraph.server.routes.common import get_db_session
from narrativegraph.server.routes.docs import get_docs_by_ids


def get_relation_by_id(db: Session, relation_id: int) -> Optional[RelationOrm]:
    """Get relation by ID"""
    return db.query(RelationOrm).filter(RelationOrm.id == relation_id).first()


def get_document_ids_by_relation(db: Session, relation_id: int, limit: Optional[int] = None) -> list[int]:
    """Get document IDs that contain the relation"""
    query = db.query(DocumentOrm.id).join(TripletOrm).filter(
        TripletOrm.relation_id == relation_id
    ).distinct()

    if limit:
        query = query.limit(limit)

    return [doc.id for doc in query.all()]


# FastAPI app
router = APIRouter()


# API Endpoints
@router.get("/{relation_id}", response_model=Details)
async def get_relation(relation_id: int, db: Session = Depends(get_db_session)):
    """Get relation details by ID"""
    relation = get_relation_by_id(db, relation_id)
    if not relation:
        raise HTTPException(status_code=404, detail="Relation not found.")

    return transform_relation_orm_to_details(relation)


@router.get("/{relation_id}/docs")
async def get_docs_by_relation(
        relation_id: int,
        limit: Optional[int] = None,
        db: Session = Depends(get_db_session)
):
    """Get documents that contain the relation"""
    doc_ids = get_document_ids_by_relation(db, relation_id, limit)

    if len(doc_ids) == 0:
        raise HTTPException(status_code=404, detail="No documents found.")

    # Call your existing getDocs function
    docs = get_docs_by_ids(db, doc_ids, None)
    return docs
