from typing import Optional

from narrativegraph.db.dtos import Document, transform_orm_to_dto
from narrativegraph.db.orms import DocumentOrm
from narrativegraph.db.service.common import OrmAssociatedService


class DocService(OrmAssociatedService):
    _orm = DocumentOrm

    def by_id(self, id_: int) -> Optional[Document]:
        with self.get_session_context():
            orm = super().by_id(id_)
            if orm:
                return transform_orm_to_dto(orm)
            return None

    def by_ids(self, ids: list[int], limit: Optional[int] = None) -> list[Document]:
        with self.get_session_context():
            return [transform_orm_to_dto(doc_orm) for doc_orm in super().by_ids(ids, limit=limit)]


    def get_docs(
        self,
    ) -> list[Document]:
        with self.get_session_context() as sc:
            return [transform_orm_to_dto(d) for d in sc.query(DocumentOrm).all()]

