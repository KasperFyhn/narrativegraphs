from abc import ABC
from dataclasses import dataclass
from typing import Literal, Optional

from spacy.tokens import Doc, Span, Token

from narrativegraphs.nlp.common.annotation import AnnotationContext, SpanAnnotation
from narrativegraphs.nlp.common.spacy import CorefMap, SpanEntityCollector
from narrativegraphs.nlp.coref.common import CoreferenceResolver
from narrativegraphs.nlp.triplets.common import Triplet
from narrativegraphs.nlp.triplets.spacy.common import SpacyTripletExtractor

_DEFAULT_RELATION_PREPOSITIONS: frozenset[str] = frozenset(
    ["as", "at", "by", "for", "from", "in", "into", "of", "on", "to", "with"]
)


# ----------------------------------------------------------------------
# Path patterns for EntityPairExtractor
# ----------------------------------------------------------------------


@dataclass(frozen=True)
class PathPattern:
    """A named dependency path pattern connecting two entity spans.

    The path from entity A's root to entity B's root passes through their
    lowest common ancestor (LCA) in the dependency tree:

        A.root -[up_deps]-> LCA <-[down_deps]- B.root

    Args:
        name: human-readable identifier
        up_deps: dep labels on each hop walking UP from A.root to LCA (exclusive)
        lca_pos: required POS tags for the LCA token
        down_deps: dep labels on each hop walking DOWN from LCA to B.root (inclusive)
        predicate: which token to use as the triplet predicate —
            "lca" uses the LCA token; "first_down" uses the first token below LCA
        swap: if True, swap subject and object in the emitted triplet (passive)
        predicate_filter: if set, the predicate token's lowercase text must be
            in this set (useful for restricting which prepositions are accepted)
    """

    name: str
    up_deps: tuple[str, ...]
    lca_pos: tuple[str, ...]
    down_deps: tuple[str, ...]
    predicate: Literal["lca", "first_down", "lca_and_first_down"]
    swap: bool = False
    predicate_filter: frozenset[str] | None = None


DEFAULT_PATH_PATTERNS: tuple[PathPattern, ...] = (
    # Standard SVO: "Alice visited London"
    PathPattern("svo", ("nsubj",), ("VERB", "AUX"), ("dobj",), "lca"),
    # Copula + noun attribute: "Alice is a doctor"
    PathPattern("copula_attr", ("nsubj",), ("VERB", "AUX"), ("attr",), "lca"),
    # Verb + prepositional object: "Alice works in London"
    PathPattern(
        "sv_prep_o", ("nsubj",), ("VERB", "AUX"), ("prep", "pobj"), "lca_and_first_down"
    ),
    # Conjunct verb + direct object: "Alice ate the apple and drank the wine"
    # predicate = the conjunct verb (first token in down_path)
    PathPattern(
        "svo_conj", ("nsubj",), ("VERB", "AUX"), ("conj", "dobj"), "first_down"
    ),
    # Conjunct verb + prepositional object: "Alice stayed home and went to Paris"
    PathPattern(
        "sv_conj_prep_o",
        ("nsubj",),
        ("VERB", "AUX"),
        ("conj", "prep", "pobj"),
        "first_down",
    ),
    # Passive with agent: "London was visited by Alice" → (Alice, visited, London)
    PathPattern(
        "passive",
        ("nsubjpass",),
        ("VERB", "AUX"),
        ("agent", "pobj"),
        "lca",
        swap=True,
    ),
    # NP-level prepositional: "Alice from Paris", "member of the council"
    PathPattern(
        "np_prep",
        (),
        ("NOUN", "PROPN"),
        ("prep", "pobj"),
        "first_down",
        predicate_filter=_DEFAULT_RELATION_PREPOSITIONS,
    ),
)


# ----------------------------------------------------------------------
# Shared base
# ----------------------------------------------------------------------


class _SpacyDepBase(SpacyTripletExtractor, ABC):
    """Shared entity-filtering logic for dependency-based extractors."""

    def __init__(
        self,
        model_name: str = None,
        named_entities: bool | tuple[int, int | None] = (1, None),
        noun_chunks: bool | tuple[int, int | None] = (2, None),
        remove_pronoun_entities: bool = True,
        split_sentence_on_double_line_break: bool = True,
        coref_resolver: CoreferenceResolver | None = None,
    ):
        super().__init__(
            model_name=model_name,
            split_sentence_on_double_line_break=split_sentence_on_double_line_break,
            coref_resolver=coref_resolver,
        )
        self.remove_pronoun_entities = remove_pronoun_entities
        self._collector = SpanEntityCollector(named_entities, noun_chunks)

    def extract_triplets_from_doc(self, doc: Doc) -> list[Triplet]:
        coref_map = self._collector.build_coref_map(doc)
        triplets = []
        for sent in doc.sents:
            sent_triplets = self.extract_triplets_from_sent(sent, coref_map)
            if sent_triplets:
                triplets.extend(sent_triplets)
        return triplets

    def _collect_entities(self, sent: Span, coref_map: CorefMap) -> list[Span]:
        return [
            s
            for s in self._collector.collect_spans(sent, coref_map)
            if not (
                self.remove_pronoun_entities
                and self._collector.is_unresolved_pronoun(s, coref_map)
            )
        ]


# ----------------------------------------------------------------------
# Top-down: verb-first traversal
# ----------------------------------------------------------------------


class DependencyGraphExtractor(_SpacyDepBase):
    def __init__(
        self,
        model_name: str = None,
        named_entities: bool | tuple[int, int | None] = (1, None),
        noun_chunks: bool | tuple[int, int | None] = (2, None),
        remove_pronoun_entities: bool = True,
        direct_objects: bool = True,
        preposition_objects: bool = True,
        passive_sentences: bool = True,
        copula_attribute: bool = True,
        conjunct_verbs: bool = True,
        prepositional_relations: bool = True,
        relation_prepositions: frozenset[str] | None = None,
        split_sentence_on_double_line_break: bool = True,
        coref_resolver: CoreferenceResolver | None = None,
    ):
        super().__init__(
            model_name=model_name,
            named_entities=named_entities,
            noun_chunks=noun_chunks,
            remove_pronoun_entities=remove_pronoun_entities,
            split_sentence_on_double_line_break=split_sentence_on_double_line_break,
            coref_resolver=coref_resolver,
        )

        self.direct_objects = direct_objects
        self.preposition_objects = preposition_objects
        self.passive_sentences = passive_sentences
        self.copula_attribute = copula_attribute
        self.conjunct_verbs = conjunct_verbs
        self.prepositional_relations = prepositional_relations
        self.relation_prepositions = (
            relation_prepositions
            if relation_prepositions is not None
            else _DEFAULT_RELATION_PREPOSITIONS
        )

    # ------------------------------------------------------------------
    # Subject / object helpers
    # ------------------------------------------------------------------

    def _find_direct_subject(self, verb_token: Token, sent: Span) -> Optional[Span]:
        for child in verb_token.children:
            if child.dep_ in ("nsubj", "nsubjpass"):
                for chunk in sent.noun_chunks:
                    if (
                        chunk.start <= child.i < chunk.end
                        and self._collector.is_allowed_entity(chunk)
                    ):
                        return chunk
        return None

    def _find_subject(
        self, verb_token: Token, sent: Span, root_verb: Optional[Token] = None
    ) -> Optional[Span]:
        """Find subject for verb_token, inheriting from root_verb for conjuncts."""
        subject = self._find_direct_subject(verb_token, sent)
        if subject is None and root_verb is not None and root_verb is not verb_token:
            subject = self._find_direct_subject(root_verb, sent)
        return subject

    def _find_object(
        self, verb_token: Token, sent: Span
    ) -> tuple[Optional[Span], bool]:
        is_passive = False
        potential_objects: list[tuple[str, Span]] = []

        for child in verb_token.children:
            if self.direct_objects and child.dep_ == "dobj":
                for chunk in sent.noun_chunks:
                    if (
                        chunk.start <= child.i < chunk.end
                        and self._collector.is_allowed_entity(chunk)
                    ):
                        potential_objects.append(("dobj", chunk))
                        break

            elif (
                self.preposition_objects
                and child.dep_ == "prep"
                and verb_token.i < child.i
            ):
                for grandchild in child.children:
                    if grandchild.dep_ == "pobj":
                        for chunk in sent.noun_chunks:
                            if (
                                chunk.start <= grandchild.i < chunk.end
                                and self._collector.is_allowed_entity(chunk)
                            ):
                                potential_objects.append(("pobj", chunk))
                                break
                        break

            elif self.passive_sentences and child.dep_ == "agent":
                is_passive = True
                for grandchild in child.children:
                    if grandchild.dep_ == "pobj":
                        for chunk in sent.noun_chunks:
                            if (
                                chunk.start <= grandchild.i < chunk.end
                                and self._collector.is_allowed_entity(chunk)
                            ):
                                potential_objects.append(("passive", chunk))
                                break
                        break

            elif self.copula_attribute and (
                child.dep_ == "attr" or child.dep_ == "acomp"
            ):
                attr_comp_span: Optional[Span] = None
                for chunk in sent.noun_chunks:
                    if (
                        chunk.start <= child.i < chunk.end
                        and self._collector.is_allowed_entity(chunk)
                    ):
                        attr_comp_span = chunk
                        break

                if attr_comp_span and self._collector.is_allowed_entity(attr_comp_span):
                    potential_objects.append(("attr", attr_comp_span))

        if not potential_objects:
            return None, False

        priority = ["dobj", "passive", "attr", "pobj"]
        potential_objects.sort(key=lambda x: priority.index(x[0]))
        return potential_objects[0][1], is_passive

    # ------------------------------------------------------------------
    # Verb discovery
    # ------------------------------------------------------------------

    def _find_verbs(self, sent: Span) -> list[Token]:
        """Return ROOT verb and, if enabled, all transitively conjunct verbs."""
        root: Optional[Token] = None
        for token in sent:
            if token.dep_ == "ROOT":
                root = token
                break
        if root is None:
            return []

        verbs = [root]
        if self.conjunct_verbs:
            queue = [root]
            while queue:
                current = queue.pop(0)
                for child in current.children:
                    if child.dep_ == "conj" and child.pos_ in ("VERB", "AUX"):
                        verbs.append(child)
                        queue.append(child)

        return verbs

    # ------------------------------------------------------------------
    # Triplet extraction
    # ------------------------------------------------------------------

    def _extract_verbal_triplets(
        self, sent: Span, coref_map: CorefMap
    ) -> list[Triplet]:
        """Extract verb-predicate triplets for ROOT and conjunct verbs."""
        triplets = []
        verbs = self._find_verbs(sent)
        if not verbs:
            return []

        root_verb = verbs[0]

        for verb_token in verbs:
            subject_span = self._find_subject(verb_token, sent, root_verb)
            obj_span, is_passive = self._find_object(verb_token, sent)

            if subject_span is None or obj_span is None:
                continue

            if self.remove_pronoun_entities and (
                self._collector.is_unresolved_pronoun(subject_span, coref_map)
                or self._collector.is_unresolved_pronoun(obj_span, coref_map)
            ):
                continue

            subject_part = self._collector.annotate(subject_span, coref_map)
            predicate_part = SpanAnnotation.from_span(verb_token)
            obj_part = self._collector.annotate(obj_span, coref_map)

            if is_passive:
                subject_part, obj_part = obj_part, subject_part

            triplets.append(
                Triplet(
                    subj=subject_part,
                    pred=predicate_part,
                    obj=obj_part,
                    context=AnnotationContext.from_span(sent),
                )
            )

        return triplets

    def _extract_np_relations(self, sent: Span, coref_map: CorefMap) -> list[Triplet]:
        """Extract NP-level prepositional relations: "Alice from Paris"."""
        triplets = []

        for chunk in sent.noun_chunks:
            if not self._collector.is_allowed_entity(chunk):
                continue
            if self.remove_pronoun_entities and self._collector.is_unresolved_pronoun(
                chunk, coref_map
            ):
                continue

            head = chunk.root

            for child in head.children:
                if child.dep_ == "prep" and child.lower_ in self.relation_prepositions:
                    for grandchild in child.children:
                        if grandchild.dep_ == "pobj":
                            for pobj_chunk in sent.noun_chunks:
                                if (
                                    pobj_chunk.start <= grandchild.i < pobj_chunk.end
                                    and self._collector.is_allowed_entity(pobj_chunk)
                                    and not (
                                        self.remove_pronoun_entities
                                        and self._collector.is_unresolved_pronoun(
                                            pobj_chunk, coref_map
                                        )
                                    )
                                    and not (
                                        chunk.start == pobj_chunk.start
                                        and chunk.end == pobj_chunk.end
                                    )
                                ):
                                    pred = SpanAnnotation(
                                        text=child.text,
                                        normalized_text=child.lemma_,
                                        start_char=child.idx,
                                        end_char=child.idx + len(child.text),
                                    )
                                    triplets.append(
                                        Triplet(
                                            subj=self._collector.annotate(
                                                chunk, coref_map
                                            ),
                                            pred=pred,
                                            obj=self._collector.annotate(
                                                pobj_chunk, coref_map
                                            ),
                                            context=AnnotationContext.from_span(sent),
                                        )
                                    )
                                    break
                            break

        return triplets

    def extract_triplets_from_sent(
        self, sent: Span, coref_map: CorefMap | None = None
    ) -> list[Triplet]:
        if coref_map is None:
            coref_map = {}
        triplets = self._extract_verbal_triplets(sent, coref_map)

        if self.prepositional_relations:
            triplets.extend(self._extract_np_relations(sent, coref_map))

        return triplets


# ----------------------------------------------------------------------
# Bottom-up: entity-pair path matching
# ----------------------------------------------------------------------


class EntityPairDependencyExtractor(_SpacyDepBase):
    """Extract triplets by matching dependency paths between entity pairs.

    For each pair of entities in a sentence, the dependency path between
    their head tokens is computed and matched against a set of allowed
    path patterns. This avoids hard-coding traversal logic per relation
    type — relation types are instead expressed as explicit path patterns.

    Guard rails (max sentence length, max entity distance) prevent the
    extractor from producing noisy results on complex parses.
    """

    def __init__(
        self,
        model_name: str = None,
        named_entities: bool | tuple[int, int | None] = (1, None),
        noun_chunks: bool | tuple[int, int | None] = (2, None),
        remove_pronoun_entities: bool = True,
        path_patterns: tuple[PathPattern, ...] | None = None,
        max_entity_distance: int = 10,
        max_sentence_length: int = 60,
        split_sentence_on_double_line_break: bool = True,
    ):
        super().__init__(
            model_name=model_name,
            named_entities=named_entities,
            noun_chunks=noun_chunks,
            remove_pronoun_entities=remove_pronoun_entities,
            split_sentence_on_double_line_break=split_sentence_on_double_line_break,
        )
        self.path_patterns = (
            path_patterns if path_patterns is not None else DEFAULT_PATH_PATTERNS
        )
        self.max_entity_distance = max_entity_distance
        self.max_sentence_length = max_sentence_length

    # ------------------------------------------------------------------
    # Path computation
    # ------------------------------------------------------------------

    @staticmethod
    def _lca_and_path(
        a: Token, b: Token
    ) -> tuple[Optional[Token], list[Token], list[Token]]:
        """Compute the LCA and dependency path between two tokens.

        Returns:
            (lca, up_path, down_path) where up_path is the list of tokens
            from a (inclusive) up to lca (exclusive), and down_path is the
            list from just below lca (inclusive) down to b (inclusive).
            Returns (None, [], []) if the tokens share no common ancestor,
            which should not happen for tokens in the same sentence.
        """
        # Build ancestor map for a: token → depth from a
        a_ancestors: dict[int, tuple[Token, int]] = {}
        current = a
        depth = 0
        while True:
            a_ancestors[current.i] = (current, depth)
            if current.head.i == current.i:  # ROOT
                break
            current = current.head
            depth += 1

        # Walk up from b until hitting a's ancestor chain
        b_to_lca: list[Token] = [b]
        current = b
        while current.i not in a_ancestors:
            if current.head.i == current.i:
                return None, [], []
            current = current.head
            b_to_lca.append(current)

        lca = current

        # up_path: tokens from a up to (not including) lca
        up_path: list[Token] = []
        current = a
        while current.i != lca.i:
            up_path.append(current)
            current = current.head

        # down_path: lca down to b (not including lca)
        down_path = list(reversed(b_to_lca[:-1]))

        return lca, up_path, down_path

    # ------------------------------------------------------------------
    # Pattern matching
    # ------------------------------------------------------------------

    @staticmethod
    def _matches(
        lca: Token,
        up_path: list[Token],
        down_path: list[Token],
        pattern: PathPattern,
    ) -> bool:
        if len(up_path) != len(pattern.up_deps):
            return False
        if len(down_path) != len(pattern.down_deps):
            return False
        if lca.pos_ not in pattern.lca_pos:
            return False
        if not all(t.dep_ == d for t, d in zip(up_path, pattern.up_deps)):
            return False
        if not all(t.dep_ == d for t, d in zip(down_path, pattern.down_deps)):
            return False
        return True

    @staticmethod
    def _resolve_predicate(
        lca: Token, down_path: list[Token], pattern: PathPattern
    ) -> Optional[SpanAnnotation]:
        """Return the predicate SpanAnnotation, or None if filtered out."""
        if pattern.predicate == "lca_and_first_down":
            prep = down_path[0]
            if pattern.predicate_filter and prep.lower_ not in pattern.predicate_filter:
                return None
            return SpanAnnotation(
                text=f"{lca.text} {prep.text}",
                normalized_text=f"{lca.lemma_} {prep.lemma_}",
                start_char=lca.idx,
                end_char=prep.idx + len(prep.text),
            )
        token = lca if pattern.predicate == "lca" else down_path[0]
        if pattern.predicate_filter and token.lower_ not in pattern.predicate_filter:
            return None
        return SpanAnnotation.from_span(token)

    # ------------------------------------------------------------------
    # Triplet extraction
    # ------------------------------------------------------------------

    def extract_triplets_from_sent(
        self, sent: Span, coref_map: CorefMap | None = None
    ) -> list[Triplet]:
        if coref_map is None:
            coref_map = {}
        if len(sent) > self.max_sentence_length:
            return []

        entities = self._collect_entities(sent, coref_map)
        if len(entities) < 2:
            return []

        triplets: set[Triplet] = set()

        for i, a_span in enumerate(entities):
            for b_span in entities[i + 1 :]:
                a_root, b_root = a_span.root, b_span.root

                if abs(a_root.i - b_root.i) > self.max_entity_distance:
                    continue

                # Check both orderings so patterns defined in canonical
                # direction (e.g. nsubj→verb←dobj) match regardless of
                # which entity appears first in the sentence.
                for src, tgt in ((a_span, b_span), (b_span, a_span)):
                    lca, up_path, down_path = self._lca_and_path(src.root, tgt.root)
                    if lca is None:
                        continue

                    for pattern in self.path_patterns:
                        if not self._matches(lca, up_path, down_path, pattern):
                            continue

                        pred = self._resolve_predicate(lca, down_path, pattern)
                        if pred is None:
                            continue

                        subj_span = tgt if pattern.swap else src
                        obj_span = src if pattern.swap else tgt

                        triplets.add(
                            Triplet(
                                subj=SpanAnnotation.from_span(subj_span),
                                pred=pred,
                                obj=SpanAnnotation.from_span(obj_span),
                                context=AnnotationContext.from_span(sent),
                            )
                        )
                        break  # first matching pattern wins per (src, tgt) direction

        return sorted(
            triplets,
            key=lambda t: (t.subj.start_char, t.pred.start_char, t.obj.start_char),
        )
