"""Integration tests for concrete coreference resolvers.

These tests require model downloads and heavy dependencies.
Run explicitly with:

    pytest tests/integration/test_coref_resolvers.py
"""

import pytest
import spacy

from narrativegraphs.nlp.entities.spacy import SpacyEntityExtractor

_TEXT = "John left for Paris. He returned after a long time."
_HE_START = _TEXT.index("He")
_HE_END = _HE_START + 2


# -----------------------------------------------------------------------
# FastCorefResolver
# -----------------------------------------------------------------------


class TestFastCorefResolver:
    @pytest.fixture(scope="class")
    def resolver(self):
        pytest.importorskip("fastcoref", reason="fastcoref not installed")
        from narrativegraphs.nlp.coref.fastcoref import FastCorefResolver

        return FastCorefResolver(model="FCoref")

    @pytest.fixture(scope="class")
    def nlp_with_coref(self, resolver):
        nlp = spacy.load("en_core_web_sm")
        resolver.add_to_pipeline(nlp)
        return nlp

    def test_resolves_pronoun_to_antecedent(self, resolver, nlp_with_coref):
        doc = nlp_with_coref(_TEXT)
        coref_map = resolver.resolve_doc(doc)
        assert (_HE_START, _HE_END) in coref_map
        assert coref_map[(_HE_START, _HE_END)] == "John"

    def test_entity_extractor_integration(self, resolver):
        extractor = SpacyEntityExtractor(noun_chunks=True, coref_resolver=resolver)
        entities = extractor.extract(_TEXT)
        texts = [e.text for e in entities]
        assert "John" in texts
        resolved = next(e for e in entities if e.start_char == _HE_START)
        assert resolved.text == "John"
