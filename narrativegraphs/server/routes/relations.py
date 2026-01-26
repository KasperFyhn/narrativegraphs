from typing import Optional

from fastapi import APIRouter, Depends

from narrativegraphs.dto.relations import RelationDetails
from narrativegraphs.server.routes.common import get_query_service
from narrativegraphs.service import QueryService

# FastAPI app
router = APIRouter()


# API Endpoints
@router.get("/{relation_id}", response_model=RelationDetails)
async def get_relation(
    relation_id: int, service: QueryService = Depends(get_query_service)
):
    """Get relation details by ID"""
    relation = service.relations.get_single(relation_id)
    return relation


@router.get("/{relation_id}/docs")
async def get_docs_by_relation(
    relation_id: int,
    limit: Optional[int] = None,
    service: QueryService = Depends(get_query_service),
):
    doc_ids = service.relations.doc_ids_by_relation(relation_id, limit=limit)
    docs = service.documents.get_multiple(doc_ids)
    return docs
