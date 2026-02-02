from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import InstrumentedAttribute

from narrativegraphs.db.cooccurrences import CooccurrenceOrm
from narrativegraphs.db.entities import EntityOrm
from narrativegraphs.db.predicates import PredicateOrm
from narrativegraphs.db.relations import RelationOrm
from narrativegraphs.db.triplets import TripletOrm
from narrativegraphs.db.tuplets import TupletOrm


class EntityCache:
    def __init__(
        self,
        session: Session,
        entity_mappings: dict[str, str],
    ):
        self._session = session
        self._entity_mappings = entity_mappings
        self._entities = self._initialize_entities()

    def _initialize_entities(self) -> dict[str, EntityOrm]:
        entities = {str(e.label): e for e in self._session.query(EntityOrm).all()}

        new_entities = []
        for mapped_entity in self._entity_mappings.values():
            if mapped_entity not in entities:
                new_entity = EntityOrm(label=mapped_entity)
                entities[mapped_entity] = new_entity
                new_entities.append(new_entity)

        if new_entities:
            self._session.add_all(new_entities)
            self._session.flush()  # Get IDs without committing

        return entities

    def get_entity_id(self, label: str) -> int:
        """Fetch an entity by label."""
        mapped_entity = self._entity_mappings[label]
        entity = self._entities.get(mapped_entity, None)
        return entity.id


class CooccurrenceCache:
    def __init__(
        self,
        session: Session,
        entity_cache: EntityCache,
        tuplets: list[TupletOrm],
    ):
        self._session = session
        self._entity_cache = entity_cache
        self._cooccurrences = self._initialize_cooccurrences(tuplets)

    def _initialize_cooccurrences(
        self, tuplets: list[TupletOrm]
    ) -> dict[tuple[int, int], CooccurrenceOrm]:
        cooccurrences = {
            (int(coc.entity_one_id), int(coc.entity_two_id)): coc
            for coc in self._session.query(CooccurrenceOrm).all()
        }

        new_cooccurrences = []
        for tuplet in tuplets:
            entity_id_1 = self._entity_cache.get_entity_id(tuplet.entity_one_span_text)
            entity_id_2 = self._entity_cache.get_entity_id(tuplet.entity_two_span_text)
            if entity_id_1 > entity_id_2:
                entity_id_2, entity_id_1 = entity_id_1, entity_id_2
            key = entity_id_1, entity_id_2
            if key not in cooccurrences:
                cooccurrence = CooccurrenceOrm(
                    entity_one_id=entity_id_1,
                    entity_two_id=entity_id_2,
                )
                cooccurrences[key] = cooccurrence
                new_cooccurrences.append(cooccurrence)

        if new_cooccurrences:
            self._session.add_all(new_cooccurrences)
            self._session.flush()

        return cooccurrences

    def get_cooccurrence_id(self, entity_id_1: int, entity_id_2: int) -> int:
        """Fetch a cooccurrence by entity pair."""
        if entity_id_1 > entity_id_2:
            entity_id_2, entity_id_1 = entity_id_1, entity_id_2
        key = entity_id_1, entity_id_2
        cooccurrence = self._cooccurrences.get(key, None)
        return cooccurrence.id


class PredicateCache:
    def __init__(
        self,
        session: Session,
        predicate_mappings: dict[str, str],
    ):
        self._session = session
        self._predicate_mappings = predicate_mappings
        self._predicates = self._initialize_predicates()

    def _initialize_predicates(self) -> dict[str, PredicateOrm]:
        predicates = {str(p.label): p for p in self._session.query(PredicateOrm).all()}

        new_predicates = []
        for mapped_predicate in self._predicate_mappings.values():
            if mapped_predicate not in predicates:
                new_predicate = PredicateOrm(label=mapped_predicate)
                predicates[mapped_predicate] = new_predicate
                new_predicates.append(new_predicate)

        if new_predicates:
            self._session.add_all(new_predicates)
            self._session.flush()

        return predicates

    def get_predicate_id(
        self,
        label: InstrumentedAttribute[str] | str,
    ):
        """Fetch a predicate by label, or create it if it doesn't exist."""
        mapped_predicate = self._predicate_mappings[label]
        predicate = self._predicates.get(mapped_predicate, None)
        return predicate.id


class RelationCache:
    def __init__(
        self,
        session: Session,
        entity_cache: EntityCache,
        predicate_cache: PredicateCache,
        triplets: list[TripletOrm],
    ):
        self._session = session
        self._entity_cache = entity_cache
        self._predicate_cache = predicate_cache

        self._relations = self._initialize_relations(triplets)

    def _initialize_relations(
        self, triplets: list[TripletOrm]
    ) -> dict[tuple[int, int, int], RelationOrm]:
        relations = {
            (int(r.subject_id), int(r.predicate_id), int(r.object_id)): r
            for r in self._session.query(RelationOrm).all()
        }

        new_relations = []
        for triplet in triplets:
            subject_id = self._entity_cache.get_entity_id(triplet.subj_span_text)
            predicate_id = self._predicate_cache.get_predicate_id(
                triplet.pred_span_text,
            )
            object_id = self._entity_cache.get_entity_id(triplet.obj_span_text)
            relation_key = (subject_id, predicate_id, object_id)
            if relation_key not in relations:
                relation = RelationOrm(
                    subject_id=subject_id,
                    predicate_id=predicate_id,
                    object_id=object_id,
                )
                relations[relation_key] = relation
                new_relations.append(relation)

        if new_relations:
            self._session.add_all(new_relations)
            self._session.flush()

        return relations

    def get_relation_id(self, subject_id: int, predicate_id: int, object_id: int):
        relation_key = (
            subject_id,
            predicate_id,
            object_id,
        )
        relation = self._relations.get(relation_key, None)
        return relation.id
