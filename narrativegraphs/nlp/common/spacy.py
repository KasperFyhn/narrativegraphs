"""Common spaCy utilities shared across entity and triplet extraction."""

import logging
from typing import Iterable

import psutil
import spacy
from spacy.tokens import Span

_logger = logging.getLogger("narrativegraphs.nlp")


def calculate_batch_size(texts: list[str], n_cpu: int = -1) -> int:
    """Simple heuristic-based batch size calculation."""
    if not texts:
        raise ValueError("No texts provided.")

    avg_length = sum(len(text) for text in texts) / len(texts)

    actual_cpu_count = (
        psutil.cpu_count() if n_cpu == -1 else min(n_cpu, psutil.cpu_count())
    )

    if avg_length < 100:
        base_size = 1000
    elif avg_length < 500:
        base_size = 500
    elif avg_length < 2000:
        base_size = 200
    elif avg_length < 5000:
        base_size = 100
    else:
        base_size = 50

    scaled_size = base_size * max(1, actual_cpu_count // 4)
    return max(10, min(scaled_size, 2000))


def ensure_spacy_model(name: str):
    """Ensure spaCy model is available, downloading if necessary."""
    try:
        return spacy.load(name)
    except OSError:
        _logger.info(
            f"First-time setup: downloading spaCy model '{name}'. "
            f"This is a one-time download (~50-500MB depending on model) "
            f"and may take a few minutes..."
        )

        try:
            spacy.cli.download(name)
            return spacy.load(name)
        except Exception as e:
            _logger.error(f"Failed to download model '{name}': {e}")
            raise RuntimeError(
                f"Could not automatically download spaCy model '{name}'.\n"
                f"Please install it manually with:\n"
                f"  python -m spacy download {name}\n"
                f"If you continue to have issues, see: "
                f"https://spacy.io/usage/models"
            ) from e


def fits_in_range(span: Span, range_: tuple[int, int | None]) -> bool:
    """Check if span length fits within the specified range."""
    lower_bound, upper_bound = range_
    return len(span) >= lower_bound and (upper_bound is None or len(span) < upper_bound)


def filter_by_range(
    spans: Iterable[Span], range_: tuple[int, int | None]
) -> list[Span]:
    """Filter spans by token length range."""
    result = []
    lower_bound, upper_bound = range_
    for span in spans:
        if len(span) >= lower_bound and (
            upper_bound is None or len(span) < upper_bound
        ):
            result.append(span)
    return result


def spans_overlap(span1: Span, span2: Span) -> bool:
    """Check if spans overlap at character level."""
    return not (
        span1.end_char <= span2.start_char or span2.end_char <= span1.start_char
    )
