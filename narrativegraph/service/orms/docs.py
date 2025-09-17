from typing import Optional

from narrativegraph.dto.documents import Document, transform_orm_to_dto
from narrativegraph.db.documents import DocumentOrm
from narrativegraph.service.common import OrmAssociatedService


class DocService(OrmAssociatedService):
    _orm = DocumentOrm

    def by_id(self, id_: int) -> Document:
        with self.get_session_context():
            return transform_orm_to_dto(super().by_id(id_))

    def by_ids(self, ids: list[int], limit: Optional[int] = None) -> list[Document]:
        with self.get_session_context():
            return [
                transform_orm_to_dto(doc_orm)
                for doc_orm in super().by_ids(ids, limit=limit)
            ]

    def get_docs(
        self,
        limit: Optional[int] = None,
    ) -> list[Document]:
        with self.get_session_context() as sc:
            query = sc.query(DocumentOrm)
            if limit:
                query = query.limit(limit)
            return [transform_orm_to_dto(d) for d in query.all()]
