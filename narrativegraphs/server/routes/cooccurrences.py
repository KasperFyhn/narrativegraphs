from typing import Optional

from fastapi import APIRouter, Depends

from narrativegraphs.dto.cooccurrences import CooccurrenceDetails
from narrativegraphs.server.routes.common import get_query_service
from narrativegraphs.service import QueryService

# FastAPI app
router = APIRouter()


# API Endpoints
@router.get("/{cooccurrence_id}", response_model=CooccurrenceDetails)
async def get_cooccurrence(
    cooccurrence_id: int, service: QueryService = Depends(get_query_service)
):
    """Get cooccurrence details by ID"""
    cooccurrence = service.cooccurrences.get_single(cooccurrence_id)
    return cooccurrence


@router.get("/{cooccurrence_id}/docs")
async def get_docs_by_cooccurrence(
    cooccurrence_id: int,
    limit: Optional[int] = None,
    service: QueryService = Depends(get_query_service),
):
    doc_ids = service.cooccurrences.doc_ids_by_cooccurrence(
        cooccurrence_id, limit=limit
    )
    docs = service.documents.get_multiple(doc_ids)
    return docs
