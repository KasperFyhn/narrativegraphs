from typing import Optional

from fastapi import APIRouter, Depends, HTTPException

from narrativegraph.dto.documents import Document
from narrativegraph.server.routes.common import get_query_service
from narrativegraph.service import QueryService

router = APIRouter()


@router.get("/{doc_id}", response_model=Document)
async def get_doc(
    doc_id: int,
    service: QueryService = Depends(get_query_service),
):
    """Get a single document by ID"""
    doc = service.documents.by_id(doc_id)
    if doc is None:
        raise HTTPException(status_code=404, detail="Could not find document!")
    return doc


@router.post("/", response_model=list[Document])
async def get_docs(
    doc_ids: list[int],
    limit: Optional[int] = None,
    service: QueryService = Depends(get_query_service),
):
    return service.documents.get_multiple(doc_ids, limit=limit)
