import multiprocessing

import spacy

from narrativegraph.extraction.common import TripletExtractor, Triplet, TripletPart
from typing import List, Tuple, Optional, Generator
from spacy.tokens import Doc, Span, Token


class DependencyGraphExtractor(TripletExtractor):

    def __init__(self, model_name: str = None):
        super().__init__()
        if model_name is None:
            model_name = "en_core_web_sm"
        self._nlp = spacy.load(model_name)

    def _extract_triplets_from_doc(self, doc: Doc) -> list[Triplet]:
        # TODO: Hacky implementation made with Gemini and should be rewritten.

        triplets = []

        for sent in doc.sents:
            # Initialize variables to store text and corresponding spaCy Span/Token objects
            # These will help us get the character indices later.
            subject_span: Optional[Span] = None
            verb_token: Optional[Token] = None
            obj_span: Optional[Span] = None

            # List to collect all tokens that form the predicate (verb, auxiliaries, prepositions, etc.)
            predicate_tokens: List[Token] = []

            is_passive = False

            # 1. Find the main verb (predicate head)
            # Prioritize the root verb of the sentence.
            for token in sent:
                if token.dep_ == "ROOT":
                    verb_token = token
                    break
            if not verb_token:
                continue  # No verb found, skip sentence

            # Add the main verb token to the predicate_tokens list
            predicate_tokens.append(verb_token)

            # 2. Find the Subject
            for child in verb_token.children:
                if child.dep_ in ["nsubj", "nsubjpass"]:
                    subj_token = child

                    for chunk in sent.noun_chunks:
                        if chunk.start <= subj_token.i < chunk.end:
                            subject_span = chunk
                            break

                    # If not found by chunk, or if it's a pronoun, use the token itself as a span
                    if subject_span is None or subj_token.pos_ == "PRON":
                        subject_span = doc[subj_token.i:subj_token.i + 1]  # Create a Span from the single token
                    break
            if subject_span is None:
                continue

            # 3. Find the Object/Prepositional Object and build predicate
            # Store potential objects as tuples of (type, Span/Token) to prioritize later
            potential_objects: List[Tuple[str, Span]] = []

            for child in verb_token.children:
                if child.dep_ == "dobj":  # Direct Object
                    for chunk in sent.noun_chunks:
                        if chunk.start <= child.i < chunk.end:
                            potential_objects.append(('dobj', chunk))
                            break
                elif child.dep_ == "attr" or child.dep_ == "acomp":  # Attribute/Complement (e.g., "is happy", "is a doctor")
                    # For attributes/complements, get the full phrase whether noun chunk or adjective
                    attr_comp_span: Optional[Span] = None
                    for chunk in sent.noun_chunks:
                        if chunk.start <= child.i < chunk.end:
                            attr_comp_span = chunk
                            break
                    if not attr_comp_span and child.pos_ == "ADJ":
                        attr_comp_span = doc[child.i:child.i + 1]  # Create a Span from the adjective token

                    if attr_comp_span:
                        potential_objects.append(('attr_acomp', attr_comp_span))

                elif child.dep_ == "xcomp":  # Open clausal complement (e.g., "likes to read books")
                    xcomp_verb_token = child
                    predicate_tokens.append(xcomp_verb_token)  # Add the xcomp verb itself

                    # Include 'to' if it's an auxiliary of the xcomp verb
                    for xcomp_aux_child in xcomp_verb_token.children:
                        if xcomp_aux_child.dep_ == "aux" and xcomp_aux_child.text.lower() == "to":
                            predicate_tokens.append(xcomp_aux_child)

                    xcomp_obj_found = False
                    for grandchild in xcomp_verb_token.children:
                        if grandchild.dep_ == "dobj":
                            for chunk in sent.noun_chunks:
                                if chunk.start <= grandchild.i < chunk.end:
                                    potential_objects.append(('xcomp_dobj', chunk))
                                    xcomp_obj_found = True
                                    break
                            break
                    if not xcomp_obj_found:  # If xcomp has no direct object, the xcomp verb itself might be the object
                        potential_objects.append(('xcomp', doc[xcomp_verb_token.i:xcomp_verb_token.i + 1]))

                elif child.dep_ == "prep" or child.dep_ == "agent":  # Prepositional objects (including passive 'by')
                    # If it's an agent, mark passive voice
                    if child.dep_ == "agent":
                        is_passive = True



                    # Find the object of the preposition
                    for grandchild in child.children:
                        if grandchild.dep_ == "pobj":
                            for chunk in sent.noun_chunks:
                                if chunk.start <= grandchild.i < chunk.end:
                                    potential_objects.append(('pobj', chunk))
                                    break
                            # if not (is_passive and child.dep_ == "agent"):
                            #     predicate_tokens.append(child)
                            break
                            # Add the preposition to the predicate tokens
                            # Only add if not passive, or if passive but it's not the 'by' agent (which is handled separately)


            # Prioritize objects: dobj > attr/acomp > xcomp_dobj > xcomp > pobj
            # This order tries to get the most "direct" object first.
            for obj_type_priority in ['dobj', 'attr_acomp', 'xcomp_dobj', 'xcomp', 'pobj']:
                found_obj = next((po_span for po_type, po_span in potential_objects if po_type == obj_type_priority),
                                 None)
                if found_obj:
                    obj_span = found_obj
                    break

            if not found_obj:
                continue

            # --- Construct TripletParts with indices ---

            subject_part = TripletPart(
                text=subject_span.text,
                start_char=subject_span.start_char,
                end_char=subject_span.end_char
            )

            # Sort predicate tokens by their start index to ensure correct text order
            predicate_tokens.sort(key=lambda t: t.idx)

            # Get the overall start and end characters for the predicate
            predicate_start_char = min(t.idx for t in predicate_tokens)
            predicate_end_char = max(t.idx + len(t.text) for t in predicate_tokens)

            # Extract the predicate text from the original document using the calculated indices
            predicate_text = doc.text[predicate_start_char:predicate_end_char]

            predicate_part = TripletPart(
                text=predicate_text,
                start_char=predicate_start_char,
                end_char=predicate_end_char
            )

            obj_part = TripletPart(
                text=obj_span.text,
                start_char=obj_span.start_char,
                end_char=obj_span.end_char
            )

            # Add the triplet if valid components are found
            # A triplet is considered valid if it has a subject and a predicate.
            # An object is optional for intransitive verbs or if not found.
            if subject_part and predicate_part and obj_part:
                if is_passive:
                    subject_part, obj_part = obj_part, subject_part
                triplets.append(Triplet(subject=subject_part, predicate=predicate_part, obj=obj_part))

        return triplets

    def extract(self, doc: str) -> list[Triplet]:
        doc = self._nlp(doc)
        return self._extract_triplets_from_doc(doc)

    def batch_extract(self, docs: list[str], n_cpu: int = None) \
            -> Generator[list[Triplet], None, None]:
        docs = self._nlp.pipe(docs, n_process=n_cpu or multiprocessing.cpu_count())
        for doc in docs:
            yield self._extract_triplets_from_doc(doc)
