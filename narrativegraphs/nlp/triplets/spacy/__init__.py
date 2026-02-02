from narrativegraphs.nlp.entities.spacy import SpacyEntityExtractor

from .dependencygraph import DependencyGraphExtractor
from .naive import NaiveSpacyTripletExtractor

__all__ = [
    "DependencyGraphExtractor",
    "NaiveSpacyTripletExtractor",
    "SpacyEntityExtractor",
]
