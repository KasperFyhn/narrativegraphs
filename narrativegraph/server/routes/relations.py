from typing import Optional

from fastapi import Depends, HTTPException, APIRouter
from sqlalchemy.orm import Session

from narrativegraph.db.orms import DocumentOrm, TripletOrm, RelationOrm
from narrativegraph.db.dtos import transform_relation_orm_to_details, Details
from narrativegraph.db.service.query import QueryService
from narrativegraph.server.routes.common import get_db_session, get_query_service
from narrativegraph.server.routes.docs import get_docs_by_ids


# FastAPI app
router = APIRouter()

# API Endpoints
@router.get("/{relation_id}", response_model=Details)
async def get_relation(relation_id: int, service: QueryService = Depends(get_query_service)):
    """Get relation details by ID"""
    relation = service.relations.by_id(relation_id)
    if not relation:
        raise HTTPException(status_code=404, detail="Relation not found.")

    return transform_relation_orm_to_details(relation)


@router.get("/{relation_id}/docs")
async def get_docs_by_relation(
        relation_id: int,
        limit: Optional[int] = None,
        service: QueryService = Depends(get_query_service)
):
    doc_ids = service.relations.doc_ids_by_relation(relation_id, limit=limit)

    if len(doc_ids) == 0:
        raise HTTPException(status_code=404, detail="No documents found.")

    docs = service.docs.by_ids(doc_ids)
    return docs
