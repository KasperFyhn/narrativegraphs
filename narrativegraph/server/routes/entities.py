from typing import Optional

from fastapi import Depends, HTTPException, APIRouter
from sqlalchemy.orm import Session

from narrativegraph.db.orms import EntityOrm, TripletOrm, DocumentOrm
from narrativegraph.db.dtos import EntityLabelsRequest, EntityLabel, Details, transform_entity_orm_to_details
from narrativegraph.db.service.query import QueryService
from narrativegraph.server.routes.common import get_db_session, get_query_service
from narrativegraph.server.routes.docs import get_docs_by_ids, get_docs

# FastAPI app
router = APIRouter()


# API Endpoints
@router.get("/{entity_id}", response_model=Details)
async def get_entity(entity_id: int, service: QueryService = Depends(get_query_service),):
    entity = service.entities.by_id(entity_id)
    if not entity:
        raise HTTPException(status_code=404, detail="Node/Entity not found.")

    return entity


@router.get("/{entity_id}/docs")
async def get_docs_by_entity(
        entity_id: int,
        limit: Optional[int] = None,
        service: QueryService = Depends(get_query_service),
):
    """Get documents that contain the entity"""
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
