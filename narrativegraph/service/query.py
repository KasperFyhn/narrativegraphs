from collections import defaultdict

from sqlalchemy import Engine, func

from narrativegraph.db.documents import DocumentCategory, DocumentOrm
from narrativegraph.db.entities import EntityOrm
from narrativegraph.db.relations import RelationOrm
from narrativegraph.dto.filter import DataBounds
from narrativegraph.service.common import DbService
from narrativegraph.service.cooccurrences import CoOccurrencesService
from narrativegraph.service.documents import DocService
from narrativegraph.service.entities import EntityService
from narrativegraph.service.graph import GraphService
from narrativegraph.service.predicates import PredicateService
from narrativegraph.service.relations import RelationService
from narrativegraph.service.triplets import TripletService


class QueryService(DbService):
    def __init__(self, engine: Engine):
        super().__init__(engine)
        self.documents = DocService(lambda: self.get_session_context())
        self.entities = EntityService(lambda: self.get_session_context())
        self.relations = RelationService(lambda: self.get_session_context())
        self.predicates = PredicateService(lambda: self.get_session_context())
        self.co_occurrences = CoOccurrencesService(lambda: self.get_session_context())
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
