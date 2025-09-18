from narrativegraph.db.relations import RelationOrm
from narrativegraph.dto.common import Details


class RelationDetails(Details):
    pass


def transform_relation_orm_to_details(relation: RelationOrm) -> RelationDetails:
    """Transform RelationOrm to Details DTO"""
    return RelationDetails(
        id=relation.id,
        label=relation.predicate.label,
        frequency=relation.frequency,
        doc_frequency=relation.doc_frequency,
        first_occurrence=relation.first_occurrence,
        last_occurrence=relation.last_occurrence,
        categories=relation.category_dict,
    )
