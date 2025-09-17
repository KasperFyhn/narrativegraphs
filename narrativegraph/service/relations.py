from typing import Optional

from narrativegraph.dto.relations import transform_relation_orm_to_details, RelationDetails
from narrativegraph.dto.common import Details
from narrativegraph.db.documents import DocumentOrm
from narrativegraph.db.triplets import TripletOrm
from narrativegraph.db.relations import RelationOrm
from narrativegraph.service.common import OrmAssociatedService


class RelationService(OrmAssociatedService):
    _orm = RelationOrm

    def by_id(self, id_: int) -> RelationDetails:
        with self.get_session_context() as sc:
            return transform_relation_orm_to_details(super().by_id(id_))

    def by_ids(self, ids: list[int], limit: Optional[int] = None) -> list[RelationDetails]:
        with self.get_session_context():
            return [
                transform_relation_orm_to_details(doc_orm)
                for doc_orm in super().by_ids(ids, limit=limit)
            ]

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
