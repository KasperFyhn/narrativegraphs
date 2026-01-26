from typing import Optional

from fastapi import APIRouter, Depends

from narrativegraphs.dto.predicates import PredicateDetails
from narrativegraphs.server.routes.common import get_query_service
from narrativegraphs.service import QueryService

# FastAPI app
router = APIRouter()


# API Endpoints
@router.get("/{predicate_id}", response_model=PredicateDetails)
async def get_predicate(
    predicate_id: int, service: QueryService = Depends(get_query_service)
):
    """Get predicate details by ID"""
    predicate = service.predicates.get_single(predicate_id)
    return predicate


@router.get("/{predicate_id}/docs")
async def get_docs_by_predicate(
    predicate_id: int,
    limit: Optional[int] = None,
    service: QueryService = Depends(get_query_service),
):
    doc_ids = service.predicates.doc_ids_by_predicate(predicate_id, limit=limit)
    docs = service.documents.get_multiple(doc_ids)
    return docs
