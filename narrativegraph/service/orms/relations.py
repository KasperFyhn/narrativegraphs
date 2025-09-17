from typing import Optional

from narrativegraph.dto.relations import transform_relation_orm_to_details
from narrativegraph.dto.common import Details
from narrativegraph.db.documents import DocumentOrm
from narrativegraph.db.triplets import TripletOrm
from narrativegraph.db.relations import RelationOrm
from narrativegraph.service.common import OrmAssociatedService


class RelationService(OrmAssociatedService):
    _orm = RelationOrm

    def by_id(self, id_: int) -> Details:
        with self.get_session_context() as sc:
            return transform_relation_orm_to_details(super().by_id(id_))

    def doc_ids_by_relation(
        self, relation_id: int, limit: Optional[int] = None
    ) -> list[int]:
        with self.get_session_context() as sc:
            query = (
                sc.query(DocumentOrm.id)
                .join(TripletOrm)
                .filter(TripletOrm.relation_id == relation_id)
                .distinct()
            )
            if limit:
                query = query.limit(limit)

        return [doc.id for doc in query.all()]
