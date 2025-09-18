from narrativegraph.nlp.extraction.common import Triplet, TripletPart
from narrativegraph.nlp.extraction.spacy.common import SpacyTripletExtractor
from typing import List, Tuple, Optional
from spacy.tokens import Span, Token


class DependencyGraphExtractor(SpacyTripletExtractor):

    def __init__(
            self,
            model_name: str = None,
            remove_pronoun_entities: bool = True,
            direct_objects: bool = True,
            preposition_objects: bool = True,
            passive_sentences: bool = True,
            copula_attribute: bool = True,
            xcomp_as_objects: bool = True,
            split_on_double_line_break: bool = True
    ):
        super().__init__(model_name)

        self.remove_pronoun_entities = remove_pronoun_entities
        self.direct_objects = direct_objects
        self.preposition_objects = preposition_objects
        self.passive_sentences = passive_sentences
        self.copula_attribute = copula_attribute
        self.xcomp_as_objects = xcomp_as_objects


    def _find_subject(self, verb_token: Token, sent: Span) -> Optional[Span]:
        subject_span: Optional[Span] = None
        for child in verb_token.children:
            if child.dep_ in ["nsubj", "nsubjpass"]:
                subj_token = child

                # find its noun chunk
                for chunk in sent.noun_chunks:
                    if chunk.start <= subj_token.i < chunk.end:
                        subject_span = chunk
                        break
        return subject_span

    def _find_object(self, verb_token: Token, sent: Span) -> tuple[Optional[Span], bool]:
        is_passive = False

        # 3. Find the Object/Prepositional Object and build predicate
        # Store potential objects as tuples of (type, Span/Token) to prioritize later
        potential_objects: List[Tuple[str, Span]] = []

        for child in verb_token.children:
            if self.direct_objects and child.dep_ == "dobj":  # Direct Object
                for chunk in sent.noun_chunks:
                    if chunk.start <= child.i < chunk.end:
                        potential_objects.append(('dobj', chunk))
                        break

            elif self.preposition_objects and child.dep_ == "prep" and verb_token.i < child.i:
                # Find the object of the preposition
                for grandchild in child.children:
                    if grandchild.dep_ == "pobj":
                        for chunk in sent.noun_chunks:
                            if chunk.start <= grandchild.i < chunk.end:
                                potential_objects.append(('pobj', chunk))
                                break
                        break

            elif self.passive_sentences and child.dep_ == "agent":
                is_passive = True
                # Find the object of the preposition
                for grandchild in child.children:
                    if grandchild.dep_ == "pobj":
                        for chunk in sent.noun_chunks:
                            if chunk.start <= grandchild.i < chunk.end:
                                potential_objects.append(('passive', chunk))
                                break
                        break

            elif self.copula_attribute and child.dep_ == "attr" or child.dep_ == "acomp":  # Attribute/Complement (e.g., "is happy", "is a doctor")
                # For attributes/complements, get the full phrase whether noun chunk or adjective
                attr_comp_span: Optional[Span] = None
                for chunk in sent.noun_chunks:
                    if chunk.start <= child.i < chunk.end:
                        attr_comp_span = chunk
                        break
                if not attr_comp_span and child.pos_ == "ADJ":
                    attr_comp_span = sent[child.i:child.i + 1]  # Create a Span from the adjective token

                if attr_comp_span:
                    potential_objects.append(('attr', attr_comp_span))

            # elif child.dep_ == "xcomp":  # Open clausal complement (e.g., "likes to read books")
            #     xcomp_verb_token = child
            #
            #     # Include 'to' if it's an auxiliary of the xcomp verb
            #     for xcomp_aux_child in xcomp_verb_token.children:
            #         if xcomp_aux_child.dep_ == "aux" and xcomp_aux_child.text.lower() == "to":
            #             predicate_tokens.append(xcomp_aux_child)
            #
            #     xcomp_obj_found = False
            #     for grandchild in xcomp_verb_token.children:
            #         if grandchild.dep_ == "dobj":
            #             for chunk in sent.noun_chunks:
            #                 if chunk.start <= grandchild.i < chunk.end:
            #                     potential_objects.append(('xcomp_dobj', chunk))
            #                     xcomp_obj_found = True
            #                     break
            #             break
            #     if not xcomp_obj_found:  # If xcomp has no direct object, the xcomp verb itself might be the object
            #         potential_objects.append(('xcomp', sent[xcomp_verb_token.i:xcomp_verb_token.i + 1]))
            #

        if not potential_objects:
            return None, False

        # Prioritize object type
        priority = ['dobj', 'passive', 'attr', 'pobj']
        potential_objects.sort(key=lambda x: priority.index(x[0]))
        obj_span = potential_objects[0][1]

        return obj_span, is_passive


    def _find_verbs(self, sent: Span) -> list[Token]:
        verbs = []
        for token in sent:
            if token.dep_ == "ROOT":
                verb_token = token
                verbs.append(verb_token)
        return verbs


    def extract_triplets_from_sent(self, sent: Span) -> list[Triplet]:
        verbs = self._find_verbs(sent)
        if not verbs:
            return []
        verb_token = verbs[0]

        subject_span = self._find_subject(verb_token, sent)
        obj_span, is_passive = self._find_object(verb_token, sent)
        if subject_span is None or obj_span is None:
            return []

        for span in (subject_span, obj_span):
            if all(t.pos_ == "PRON" for t in span):
                return []

        subject_part = TripletPart.from_span(subject_span)
        predicate_part = TripletPart.from_span(verb_token)
        obj_part = TripletPart.from_span(obj_span)

        if subject_part and predicate_part and obj_part:
            if is_passive:
                subject_part, obj_part = obj_part, subject_part
            return [Triplet(subj=subject_part, pred=predicate_part, obj=obj_part)]
        else:
            return []

