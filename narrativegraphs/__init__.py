from narrativegraphs.dto.filter import GraphFilter
from narrativegraphs.nlp.entities.spacy import SpacyEntityExtractor
from narrativegraphs.nlp.mapping.linguistic import SubgramStemmingMapper
from narrativegraphs.nlp.triplets.spacy.dependencygraph import DependencyGraphExtractor
from narrativegraphs.nlp.tuplets.cooccurrences import ChunkCooccurrenceExtractor

from .graphs import CooccurrenceGraph, NarrativeGraph

__all__ = [
    "GraphFilter",
    "CooccurrenceGraph",
    "NarrativeGraph",
    "DependencyGraphExtractor",
    "ChunkCooccurrenceExtractor",
    "SubgramStemmingMapper",
    "SpacyEntityExtractor",
]

try:
    from ._version import version as __version__
except ImportError:
    __version__ = "unknown"
