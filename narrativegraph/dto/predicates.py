from narrativegraph.db.relations import RelationOrm
from narrativegraph.dto.common import Details


class PredicateDetails(Details):
    pass


def transform_predicate_orm_to_details(predicate: PredicateDetails) -> PredicateDetails:
    """Transform RelationOrm to Details DTO"""
    return PredicateDetails(
        id=predicate.id,
        label=predicate.label,
        frequency=predicate.term_frequency,
        doc_frequency=predicate.doc_frequency,
        first_occurrence=predicate.first_occurrence,
        last_occurrence=predicate.last_occurrence,
        categories=predicate.category_dict,
    )
