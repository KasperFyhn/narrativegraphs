from typing import Optional

from fastapi import Depends, HTTPException, APIRouter

from narrativegraph.dto.entities import EntityLabel, EntityLabelsRequest
from narrativegraph.dto.common import Details
from narrativegraph.service import QueryService
from narrativegraph.server.routes.common import get_query_service

# FastAPI app
router = APIRouter()


@router.get("/{entity_id}", response_model=Details)
async def get_entity(entity_id: int, service: QueryService = Depends(get_query_service),):
    entity = service.entities.by_id(entity_id)
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

    docs = service.docs.by_ids(doc_ids, limit=limit)
    return docs


@router.post("/labels", response_model=list[EntityLabel])
async def get_entity_labels(
        request: EntityLabelsRequest, service: QueryService = Depends(get_query_service),
):
    """Get entity labels by IDs"""
    entity_labels = service.entities.labels_by_ids(request.ids)

    if len(entity_labels) == 0:
        raise HTTPException(status_code=404, detail="No entities found.")

    return entity_labels
