from narrativegraphs.nlp.triplets.common import TripletExtractor
from narrativegraphs.nlp.triplets.llm import LlmTripletExtractor
from narrativegraphs.nlp.triplets.spacy.dependencygraph import (
    DependencyGraphExtractor,
)

__all__ = [
    "TripletExtractor",
    "DependencyGraphExtractor",
    "LlmTripletExtractor",
]
