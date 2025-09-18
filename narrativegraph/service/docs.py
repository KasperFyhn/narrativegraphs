from typing import Optional

import pandas as pd
from sqlalchemy import select

from narrativegraph.dto.documents import Document, transform_orm_to_dto
from narrativegraph.db.documents import DocumentOrm, DocumentCategory
from narrativegraph.service.common import OrmAssociatedService


class DocService(OrmAssociatedService):
    _orm = DocumentOrm
    _category_orm = DocumentCategory

    def as_df(self) -> pd.DataFrame:
        with self.get_session_context() as session:
            engine = session.get_bind()

            entities_df = pd.read_sql(
                select(
                    DocumentOrm.id.label("id"),
                    DocumentOrm.str_id.label("str_id"),
                    DocumentOrm.text.label("text"),
                    DocumentOrm.timestamp.label("timestamp"),
                ),
                engine,
            )

            with_categories = self._add_category_columns(entities_df)
        cleaned = with_categories.dropna(axis=1, how="all")

        return cleaned

    def by_id(self, id_: int) -> Document:
        return self._get_by_id_and_transform(id_, transform_orm_to_dto)

    def by_ids(self, ids: list[int], limit: Optional[int] = None) -> list[Document]:
        return self._get_multiple_by_ids_and_transform(
            ids, transform_orm_to_dto, limit=limit
        )

    def get_docs(
        self,
        limit: Optional[int] = None,
    ) -> list[Document]:
        with self.get_session_context() as sc:
            query = sc.query(DocumentOrm)
            if limit:
                query = query.limit(limit)
            return [transform_orm_to_dto(d) for d in query.all()]
