from narrativegraphs.nlp.extraction.common import TripletExtractor
from narrativegraphs.nlp.extraction.entities import EntityExtractor
from narrativegraphs.nlp.extraction.spacy.dependencygraph import (
    DependencyGraphExtractor,
)
from narrativegraphs.nlp.extraction.spacy.entities import SpacyEntityExtractor

__all__ = [
    "TripletExtractor",
    "DependencyGraphExtractor",
    "EntityExtractor",
    "SpacyEntityExtractor",
]
