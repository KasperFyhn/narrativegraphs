from typing import Optional

from fastapi import Depends, HTTPException, APIRouter

from narrativegraph.dto.relations import transform_relation_orm_to_details
from narrativegraph.dto.common import Details
from narrativegraph.service import QueryService
from narrativegraph.server.routes.common import get_query_service

# FastAPI app
router = APIRouter()

# API Endpoints
@router.get("/{relation_id}", response_model=Details)
async def get_relation(relation_id: int, service: QueryService = Depends(get_query_service)):
    """Get relation details by ID"""
    relation = service.relations.by_id(relation_id)
    return relation


@router.get("/{relation_id}/docs")
async def get_docs_by_relation(
        relation_id: int,
        limit: Optional[int] = None,
        service: QueryService = Depends(get_query_service)
):
    doc_ids = service.relations.doc_ids_by_relation(relation_id, limit=limit)
    docs = service.docs.by_ids(doc_ids)
    return docs
