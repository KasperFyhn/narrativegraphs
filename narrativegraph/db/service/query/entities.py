from typing import Optional

from narrativegraph.db.dtos import (
    Node,
    Details,
    transform_entity_orm_to_details,
    EntityLabel,
)
from narrativegraph.db.orms import EntityOrm, DocumentOrm, TripletOrm
from narrativegraph.db.service.common import OrmAssociatedService


class EntityService(OrmAssociatedService):
    _orm = EntityOrm

    def by_id(self, id_: int) -> Optional[Details]:
        with self.get_session_context():
            orm = super().by_id(id_)
            if orm:
                return transform_entity_orm_to_details(orm)
            return None

    def doc_ids_by_entity(self, entity_id: int, limit: Optional[int] = None) -> list[int]:
        with self.get_session_context() as sc:
            query = (
                sc.query(DocumentOrm.id)
                .join(TripletOrm)
                .filter(
                    (TripletOrm.subject_id == entity_id)
                    | (TripletOrm.object_id == entity_id)
                )
                .distinct()
            )
            if limit:
                query = query.limit(limit)

        return [doc.id for doc in query.all()]

    def get_entities(
        self,
    ) -> list[Node]:
        with self.get_session_context() as sc:
            return [
                Node(id=e.id, label=e.label, term_frequency=e.term_frequency)
                for e in sc.query(EntityOrm).all()
            ]

    def labels_by_ids(
        self, entity_ids: list[int]
    ) -> list[EntityLabel]:
        with self.get_session_context() as sc:
            entities = (
                sc.query(EntityOrm.id, EntityOrm.label)
                .filter(EntityOrm.id.in_(entity_ids))
                .all()
            )

            return [EntityLabel(id=entity.id, label=entity.label) for entity in entities]
