from sqlalchemy.orm import Session, InstrumentedAttribute
from tqdm import tqdm

from narrativegraph.db.orms import RelationOrm, EntityOrm


class EntityAndRelationCache:

    def __init__(self, session: Session, entity_mappings: dict[str, str],
                 predicate_mappings: dict[str, str]):
        self._session = session
        self._entities = {str(e.label): e for e in session.query(EntityOrm).all()}
        self._relations = {
            (int(r.subject_id), str(r.label), int(r.object_id)): r  # noqa
            for r in session.query(RelationOrm).all()
        }

        self._entity_mappings = entity_mappings
        self._predicate_mappings = predicate_mappings

    def get_or_create_entity(self, label: InstrumentedAttribute[str] | str):
        """Fetch an entity by label, or create it if it doesn't exist."""
        mapped_entity = self._entity_mappings[label]

        entity = self._entities.get(mapped_entity, None)
        if entity is None:
            entity = EntityOrm(label=mapped_entity)
            self._session.add(entity)
            self._session.flush()  # Get the ID immediately
            self._entities[mapped_entity] = entity  # noqa
        return entity.id

    def get_or_create_relation(
            self,
            subject_id: int,
            object_id: int,
            predicate_label: InstrumentedAttribute[str] | str,
    ):
        """Fetch a relation by label, or create it if it doesn't exist."""
        mapped_predicate = self._predicate_mappings[predicate_label]
        relation_key = (
            subject_id,
            mapped_predicate,
            object_id,
        )

        relation = self._relations.get(relation_key, None)
        if relation is None:
            relation = RelationOrm(
                label=mapped_predicate,
                subject_id=subject_id,
                object_id=object_id,
            )
            self._session.add(relation)
            self._session.flush()  # Get the ID immediately
            self._relations[relation_key] = relation  # noqa
        return relation.id

    def update_entity_info(self):
        for entity in tqdm(self._entities.values(), desc="Updating entity info"):
            as_subject = len(entity.subject_triplets)  # noqa
            as_object = len(entity.object_triplets)  # noqa

            entity.term_frequency = as_subject + as_object

            triplets = entity.subject_triplets + entity.object_triplets
            entity.doc_frequency = len(
                set(t.doc_id for t in triplets),
            )
            entity.categories = ','.join(
                sorted(t.category for t in triplets
                if t.category is not None)
            )
            dates = [
                t.timestamp for t in triplets
                if t.timestamp is not None
            ]
            entity.first_occurrence = min(dates, default=None)
            entity.last_occurrence = max(dates, default=None)
            # super_entity = self._mappings.get_super_entity(entity.label)
            # if super_entity is not None:
            #     entity.supernode_id = self.get_or_create_entity(super_entity)
            #     entity.is_supernode = entity.id == entity.supernode_id
        self._session.commit()

    def update_relation_info(self):
        for relation in tqdm(
                self._relations.values(),
                desc="Updating relation info",
        ):
            relation.term_frequency = len(relation.triplets)  # noqa
            relation.doc_frequency = len(set(t.doc_id for t in relation.triplets))
            relation.categories = ','.join(
                sorted(t.category for t in relation.triplets
                if t.category is not None)
            )
            dates = [t.timestamp for t in relation.triplets
                     if t.timestamp is not None]
            relation.first_occurrence = min(dates, default=None)
            relation.last_occurrence = max(dates, default=None)
        self._session.commit()
