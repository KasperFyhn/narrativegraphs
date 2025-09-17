from typing import Optional

from narrativegraph.db.documents import DocumentOrm
from narrativegraph.db.triplets import TripletOrm
from narrativegraph.db.predicates import PredicateOrm
from narrativegraph.dto.predicates import (
    transform_predicate_orm_to_details,
    PredicateDetails,
)
from narrativegraph.service.common import OrmAssociatedService


class PredicateService(OrmAssociatedService):

    _orm = PredicateOrm

    def by_id(self, id_: int) -> PredicateDetails:
        with self.get_session_context() as sc:
            return transform_predicate_orm_to_details(super().by_id(id_))


    def by_ids(self, ids: list[int], limit: Optional[int] = None) -> list[PredicateDetails]:
        with self.get_session_context():
            return [
                transform_predicate_orm_to_details(doc_orm)
                for doc_orm in super().by_ids(ids, limit=limit)
            ]

    def doc_ids_by_predicate(
        self, predicate_id: int, limit: Optional[int] = None
    ) -> list[int]:
        with self.get_session_context() as sc:
            query = (
                sc.query(DocumentOrm.id)
                .join(TripletOrm)
                .filter(TripletOrm.predicate_id == predicate_id)
                .distinct()
            )
            if limit:
                query = query.limit(limit)

        return [doc.id for doc in query.all()]
