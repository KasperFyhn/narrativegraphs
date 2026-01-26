from typing import Optional

import pandas as pd
from sqlalchemy import select

from narrativegraphs.db.documents import DocumentCategory, DocumentOrm
from narrativegraphs.dto.documents import Document
from narrativegraphs.service.common import OrmAssociatedService


class DocService(OrmAssociatedService):
    _orm = DocumentOrm
    _category_orm = DocumentCategory

    def as_df(self) -> pd.DataFrame:
        with self._get_session_context() as session:
            engine = session.get_bind()

            df = pd.read_sql(
                select(
                    DocumentOrm.id.label("id"),
                    DocumentOrm.str_id.label("str_id"),
                    DocumentOrm.text.label("text"),
                    DocumentOrm.timestamp.label("timestamp"),
                ),
                engine,
            )

            with_categories = self._add_category_columns(df)
        cleaned = with_categories.dropna(axis=1, how="all")

        return cleaned

    def get_single(self, id_: int) -> Document:
        return self._get_by_id_and_transform(id_, Document.from_orm)

    def get_multiple(
        self, ids: list[int] = None, limit: Optional[int] = None
    ) -> list[Document]:
        return self._get_multiple_by_ids_and_transform(
            Document.from_orm, ids=ids, limit=limit
        )

    def get_docs(
        self,
        limit: Optional[int] = None,
    ) -> list[Document]:
        with self._get_session_context() as sc:
            query = sc.query(DocumentOrm)
            if limit:
                query = query.limit(limit)
            return [Document.from_orm(d) for d in query.all()]
