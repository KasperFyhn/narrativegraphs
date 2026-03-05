from spacy.language import Language
from spacy.tokens import Doc

from narrativegraphs.nlp.coref.common import CoreferenceResolver


class FastCorefResolver(CoreferenceResolver):
    """Coreference resolver using the fastcoref spaCy component.

    Adds itself to the spaCy pipeline via add_to_pipeline. After processing,
    reads coreference clusters from doc._.coref_clusters (character span tuples).

    Supports FCoref (fast) and LingMess (more accurate) models.

    Requires optional dependency: fastcoref>=2.1.3
    """

    def __init__(self, model: str = "FCoref"):
        """
        Args:
            model: "FCoref" for the fast model or "LingMess" for the accurate model
        """
        try:
            import datasets
            from fastcoref import (
                spacy_component,  # noqa: F401 — registers the component
            )

            datasets.disable_progress_bars()
        except ImportError:
            raise ImportError(
                "fastcoref is required for FastCorefResolver. "
                "Install it with: pip install 'narrativegraphs[coref-fastcoref]'"
            )
        if model not in ("FCoref", "LingMess"):
            raise ValueError(
                f"Unknown fastcoref model: {model!r}. Use 'FCoref' or 'LingMess'."
            )
        self._model = model

    def add_to_pipeline(self, nlp: Language) -> None:
        if "fastcoref" not in nlp.pipe_names:
            nlp.add_pipe(
                "fastcoref",
                config={
                    "model_architecture": self._model,
                    "enable_progress_bar": False,
                },
            )

    @staticmethod
    def _is_pronoun(doc: Doc, start: int, end: int) -> bool:
        span = doc.char_span(start, end)
        return span is not None and all(t.pos_ == "PRON" for t in span)

    def resolve_doc(self, doc: Doc) -> dict[tuple[int, int], str]:
        coref_map: dict[tuple[int, int], str] = {}
        for cluster in doc._.coref_clusters:
            if not cluster:
                continue
            # Use the first non-pronoun mention as antecedent so that cataphoric
            # references ("Before he left, John …") resolve correctly.
            head = next(
                ((s, e) for s, e in cluster if not self._is_pronoun(doc, s, e)),
                None,
            )
            if head is None:
                continue
            head_start, head_end = head
            antecedent_text = doc.text[head_start:head_end]
            for start, end in cluster:
                if (start, end) != (head_start, head_end):
                    coref_map[(start, end)] = antecedent_text
        return coref_map
