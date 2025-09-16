from typing import Optional

from fastapi import Depends, HTTPException, APIRouter
from sqlalchemy.orm import Session

from narrativegraph.db.orms import EntityOrm, TripletOrm, DocumentOrm
from narrativegraph.db.dtos import EntityLabelsRequest, EntityLabel, Details, transform_entity_orm_to_details
from narrativegraph.server.routes.common import get_db_session
from narrativegraph.server.routes.docs import get_docs_by_ids


def get_entity_by_id(entity_id: int, db: Session) -> Optional[EntityOrm]:
    """Get entity by ID"""
    return db.query(EntityOrm).filter(EntityOrm.id == entity_id).first()


def get_document_ids_by_entity(entity_id: int, limit: Optional[int],
                               db: Session = Depends(get_db_session)) -> list[int]:
    """Get document IDs that contain the entity as subject or object"""

    query = db.query(DocumentOrm.id).join(TripletOrm).filter(
        (TripletOrm.subject_id == entity_id) | (TripletOrm.object_id == entity_id)
    ).distinct()

    if limit:
        query = query.limit(limit)

    return [doc.id for doc in query.all()]


def get_entity_labels_by_ids(entity_ids: list[int], db: Session = Depends(get_db_session)) -> list[
    EntityLabel]:
    """Get entity labels by IDs"""
    entities = db.query(EntityOrm.id, EntityOrm.label).filter(
        EntityOrm.id.in_(entity_ids)
    ).all()

    return [EntityLabel(id=entity.id, label=entity.label) for entity in entities]


# FastAPI app
router = APIRouter()


# API Endpoints
@router.get("/{entity_id}", response_model=Details)
async def get_entity(entity_id: int, db: Session = Depends(get_db_session)):
    """Get entity details by ID"""

    entity = get_entity_by_id(entity_id, db)
    if not entity:
        raise HTTPException(status_code=404, detail="Node/Entity not found.")

    return transform_entity_orm_to_details(entity)


@router.get("/{entity_id}/docs")
async def get_docs_by_entity(
        entity_id: int,
        limit: Optional[int] = None,
        db: Session = Depends(get_db_session)
):
    """Get documents that contain the entity"""
    doc_ids = get_document_ids_by_entity(entity_id, limit, db)

    if len(doc_ids) == 0:
        raise HTTPException(status_code=404, detail="No documents found.")

    # Call your existing getDocs function
    docs = get_docs_by_ids(db, doc_ids, None)
    return docs


@router.post("/labels", response_model=list[EntityLabel])
async def get_entity_labels(
        request: EntityLabelsRequest, db: Session = Depends(get_db_session)
):
    """Get entity labels by IDs"""
    entity_labels = get_entity_labels_by_ids(request.ids, db)

    if len(entity_labels) == 0:
        raise HTTPException(status_code=404, detail="No entities found.")

    return entity_labels
