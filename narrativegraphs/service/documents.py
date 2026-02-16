from functools import partial
from typing import Optional

import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from narrativegraphs.db.documents import DocumentCategory, DocumentOrm
from narrativegraphs.db.triplets import TripletOrm
from narrativegraphs.db.tuplets import TupletOrm
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
        """Get a single document without relations."""
        with self._get_session_context() as sc:
            query = sc.query(self._orm).options(selectinload(DocumentOrm.categories))
            entry = query.get(id_)
            if entry is None:
                from narrativegraphs.errors import EntryNotFoundError

                raise EntryNotFoundError(
                    f"No entry with id '{id_}' in table {self._orm.__tablename__}"
                )
            return Document.from_orm(entry)

    @staticmethod
    def _build_options(
        include_triplets: bool = False,
        include_tuplets: bool = False,
        include_mentions: bool = False,
    ) -> list:
        """Build SQLAlchemy eager loading options based on what's needed."""
        options = [selectinload(DocumentOrm.categories)]

        if include_triplets:
            options.extend(
                [
                    selectinload(DocumentOrm.triplets).selectinload(
                        TripletOrm.subject_occurrence
                    ),
                    selectinload(DocumentOrm.triplets).selectinload(
                        TripletOrm.object_occurrence
                    ),
                ]
            )

        if include_tuplets:
            options.extend(
                [
                    selectinload(DocumentOrm.tuplets).selectinload(
                        TupletOrm.entity_one_occurrence
                    ),
                    selectinload(DocumentOrm.tuplets).selectinload(
                        TupletOrm.entity_two_occurrence
                    ),
                ]
            )

        if include_mentions:
            options.append(selectinload(DocumentOrm.entity_occurrences))

        return options

    def get_multiple(
        self,
        ids: list[int] = None,
        limit: Optional[int] = None,
        include_triplets: bool = False,
        include_tuplets: bool = False,
        include_mentions: bool = False,
    ) -> list[Document]:
        """Get multiple documents with optional relation loading."""
        options = self._build_options(
            include_triplets, include_tuplets, include_mentions
        )
        transform = partial(
            Document.from_orm,
            include_triplets=include_triplets,
            include_tuplets=include_tuplets,
            include_mentions=include_mentions,
        )
        with self._get_session_context() as sc:
            query = sc.query(self._orm).options(*options)
            if ids is not None:
                query = query.filter(self._orm.id.in_(ids))
            if limit:
                query = query.limit(limit)
            entries = query.all()
            return [transform(entry) for entry in entries]

    def get_multiple_with_triplets(
        self, ids: list[int] = None, limit: Optional[int] = None
    ) -> list[Document]:
        """Get documents with triplets only."""
        return self.get_multiple(ids=ids, limit=limit, include_triplets=True)

    def get_multiple_with_tuplets(
        self, ids: list[int] = None, limit: Optional[int] = None
    ) -> list[Document]:
        """Get documents with tuplets only."""
        return self.get_multiple(ids=ids, limit=limit, include_tuplets=True)

    def get_multiple_with_mentions(
        self, ids: list[int] = None, limit: Optional[int] = None
    ) -> list[Document]:
        """Get documents with entity mentions only."""
        return self.get_multiple(ids=ids, limit=limit, include_mentions=True)
