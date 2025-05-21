from typing import NamedTuple, Generator


# Define a NamedTuple for a part of the triplet with its text and character indices
class TripletPart(NamedTuple):
    text: str
    start_char: int
    end_char: int


# Define a NamedTuple for the full triplet, composed of TripletParts
class Triplet(NamedTuple):
    subject: TripletPart
    predicate: TripletPart
    obj: TripletPart  # Naming 'obj' to avoid conflict with Python's built-in 'object'


class TripletExtractor:

    def __init__(self):
        pass

    def extract(self, doc: str) -> list[Triplet]:
        pass

    def batch_extract(self, docs: list[str], n_cpu: int = None) \
            -> Generator[list[Triplet], None, None]:
        for doc in docs:
            yield self.extract(doc)
