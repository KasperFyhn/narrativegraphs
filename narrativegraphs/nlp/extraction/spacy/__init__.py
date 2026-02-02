from .dependencygraph import DependencyGraphExtractor
from .entities import SpacyEntityExtractor
from .naive import NaiveSpacyTripletExtractor

__all__ = [
    "DependencyGraphExtractor",
    "NaiveSpacyTripletExtractor",
    "SpacyEntityExtractor",
]
