from fastapi_camelcase import CamelModel


class SpanEntity(CamelModel):
    id: int
    start: int
    end: int


class Triplet(CamelModel):
    subject: SpanEntity
    predicate: SpanEntity
    object: SpanEntity
