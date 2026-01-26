from collections import defaultdict

from sqlalchemy import Engine, func

from narrativegraphs.db.documents import DocumentCategory, DocumentOrm
from narrativegraphs.db.entities import EntityOrm
from narrativegraphs.db.relations import RelationOrm
from narrativegraphs.dto.filter import DataBounds
from narrativegraphs.service.common import DbService
from narrativegraphs.service.cooccurrences import CooccurrenceService
from narrativegraphs.service.documents import DocService
from narrativegraphs.service.entities import EntityService
from narrativegraphs.service.graph import GraphService
from narrativegraphs.service.predicates import PredicateService
from narrativegraphs.service.relations import RelationService
from narrativegraphs.service.triplets import TripletService


class QueryService(DbService):
    def __init__(self, engine: Engine):
        super().__init__(engine)
        self.documents = DocService(lambda: self.get_session_context())
        self.entities = EntityService(lambda: self.get_session_context())
        self.relations = RelationService(lambda: self.get_session_context())
        self.predicates = PredicateService(lambda: self.get_session_context())
        self.cooccurrences = CooccurrenceService(lambda: self.get_session_context())
        self.triplets = TripletService(lambda: self.get_session_context())
        self.graph = GraphService(lambda: self.get_session_context())

    def _compile_categories(self) -> dict[str, list[str]]:
        with self.get_session_context() as db:
            categories = defaultdict(set)
            for doc_category in db.query(DocumentCategory).all():
                categories[doc_category.name].add(doc_category.value)
            return {name: list(values) for name, values in categories.items()}

    def get_bounds(self):
        with self.get_session_context() as db:
            categories = self._compile_categories()
            if not categories:
                categories = None
            return DataBounds(
                minimum_possible_node_frequency=db.query(
                    func.min(EntityOrm.frequency)
                ).scalar(),
                maximum_possible_node_frequency=db.query(
                    func.max(EntityOrm.frequency)
                ).scalar(),
                minimum_possible_edge_frequency=db.query(
                    func.min(RelationOrm.frequency)
                ).scalar(),
                maximum_possible_edge_frequency=db.query(
                    func.max(RelationOrm.frequency)
                ).scalar(),
                categories=categories,
                earliest_date=db.query(func.min(DocumentOrm.timestamp)).scalar()
                or None,
                latest_date=db.query(func.max(DocumentOrm.timestamp)).scalar() or None,
            )
