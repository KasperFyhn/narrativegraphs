from abc import ABC, abstractmethod

from spacy.language import Language
from spacy.tokens import Doc


class CoreferenceResolver(ABC):
    def add_to_pipeline(self, nlp: Language) -> None:
        """Add this resolver as a spaCy pipe component (default: no-op)."""
        pass

    @abstractmethod
    def resolve_doc(self, doc: Doc) -> dict[tuple[int, int], str]:
        """Return {(start_char, end_char): antecedent_text} for all coreferent
        mentions."""
