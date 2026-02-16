from typing import Optional

from fastapi import APIRouter, Depends, HTTPException

from narrativegraphs.dto.entities import (
    EntityDetails,
    EntityDocsRequest,
    EntityLabel,
    EntityLabelsRequest,
)
from narrativegraphs.server.routes.common import get_query_service
from narrativegraphs.service import QueryService

# FastAPI app
router = APIRouter()


@router.get("/{entity_id}", response_model=EntityDetails)
async def get_entity(
    entity_id: int,
    service: QueryService = Depends(get_query_service),
):
    entity = service.entities.get_single(entity_id)
    return entity


@router.get("/{entity_id}/docs")
async def get_docs_by_entity(
    entity_id: int,
    limit: Optional[int] = None,
    service: QueryService = Depends(get_query_service),
):
    doc_ids = service.entities.doc_ids_by_entity(entity_id, limit=limit)

    if len(doc_ids) == 0:
        raise HTTPException(status_code=404, detail="No documents found.")

    docs = service.documents.get_multiple_with_mentions(doc_ids, limit=limit)
    return docs


@router.get("/search/{search_string}")
async def search_entities(
    search_string: str,
    limit: Optional[int] = None,
    service: QueryService = Depends(get_query_service),
):
    return service.entities.search(search_string, limit=limit)


@router.post("/labels", response_model=list[EntityLabel])
async def get_entity_labels(
    request: EntityLabelsRequest,
    service: QueryService = Depends(get_query_service),
):
    """Get entity labels by IDs"""
    entity_labels = service.entities.labels_by_ids(request.ids)

    if len(entity_labels) == 0:
        raise HTTPException(status_code=404, detail="No entities found.")

    return entity_labels


@router.post("/docs")
async def get_docs_by_entities(
    request: EntityDocsRequest,
    service: QueryService = Depends(get_query_service),
):
    """Get documents containing any of the specified entities"""
    doc_ids = service.entities.doc_ids_by_entities(
        request.entity_ids, limit=request.limit
    )

    if len(doc_ids) == 0:
        raise HTTPException(status_code=404, detail="No documents found.")

    if request.connection_type == "cooccurrence":
        docs = service.documents.get_multiple_with_tuplets(doc_ids, limit=request.limit)
    else:
        docs = service.documents.get_multiple_with_triplets(
            doc_ids, limit=request.limit
        )
    return docs
