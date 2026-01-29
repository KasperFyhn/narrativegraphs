from narrativegraphs.dto.filter import GraphFilter
from narrativegraphs.narrativegraph import NarrativeGraph

__all__ = ["NarrativeGraph", "GraphFilter"]

try:
    from ._version import version as __version__
except ImportError:
    __version__ = "unknown"
