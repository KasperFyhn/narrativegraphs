from narrativegraphs.dto.filter import GraphFilter

from .graphs import CooccurrenceGraph, NarrativeGraph

__all__ = ["GraphFilter"]

try:
    from ._version import version as __version__
except ImportError:
    __version__ = "unknown"
