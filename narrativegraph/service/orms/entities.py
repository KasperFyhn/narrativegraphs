from typing import Optional

from narrativegraph.dto.entities import EntityLabel, transform_entity_orm_to_details
from narrativegraph.dto.graph import Node
from narrativegraph.dto.common import Details
from narrativegraph.db.documents import DocumentOrm
from narrativegraph.db.triplets import TripletOrm
from narrativegraph.db.entities import EntityOrm
from narrativegraph.service.common import OrmAssociatedService


class EntityService(OrmAssociatedService):
    _orm = EntityOrm

    def by_id(self, id_: int) -> Details:
        with self.get_session_context():
            return transform_entity_orm_to_details(super().by_id(id_))

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
