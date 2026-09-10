# NLP Layer

This guide provides an overview of the NLP layer in `narrativegraphs/nlp/`.

## Pipelines

The NLP layer provides two main pipelines that orchestrate the full extraction workflow:

| Pipeline                 | Purpose                              | Extracts                 |
| ------------------------ | ------------------------------------ | ------------------------ |
| **Pipeline**             | Full narrative graph extraction      | Triplets + cooccurrences |
| **CooccurrencePipeline** | Simpler cooccurrence-only extraction | Entities + cooccurrences |

Both pipelines handle:

1. Adding documents to the database
2. Extracting and storing annotations
3. Mapping surface forms to canonical entities/predicates
4. Calculating statistics

### Pipeline (Full)

Uses a `TripletExtractor` to extract subject-predicate-object triplets, then derives entities from those triplets. Also extracts cooccurrences between entities.

Default components:

- Triplet extraction: `DependencyGraphExtractor` (default; `EntityPairDependencyExtractor` is an alternative)
- Cooccurrence extraction: `ChunkCooccurrenceExtractor`
- Entity mapping: `SubgramLemmatizationMapper("noun")`
- Predicate mapping: `SubgramLemmatizationMapper("verb")`

### CooccurrencePipeline

Uses an `EntityExtractor` directly to find entities, then extracts cooccurrences between them. Skips triplet extraction entirely.

Default components:

- Entity extraction: `SpacyEntityExtractor`
- Cooccurrence extraction: `ChunkCooccurrenceExtractor`
- Entity mapping: `SubgramLemmatizationMapper("noun")`

## Extraction Components

### Entity Extraction (`entities/`)

| Class                    | Description                                                        |
| ------------------------ | ------------------------------------------------------------------ |
| **EntityExtractor**      | Abstract base class                                                |
| **SpacyEntityExtractor** | Uses spaCy NER and/or noun chunks with configurable length filters |

`SpacyEntityExtractor` features:

- Configurable NER and noun chunk extraction
- Token length filtering (min/max tokens)
- Greedy non-overlapping span selection (NER takes priority)
- Pronoun filtering
- Parallel batch processing

### Triplet Extraction (`triplets/`)

| Class                             | Description                                                                             |
| --------------------------------- | --------------------------------------------------------------------------------------- |
| **TripletExtractor**              | Abstract base class                                                                     |
| **DependencyGraphExtractor**      | Verb-first (top-down from ROOT); fine-grained boolean flags per relation type           |
| **EntityPairDependencyExtractor** | Entity-pair (bottom-up, path matching); declarative `PathPattern` list; sentence guards |
| **LlmTripletExtractor**           | Prompts an LLM with a plain-language instruction; one request per document              |

Triplets consist of:

- `subj`: Subject entity (SpanAnnotation)
- `pred`: Predicate/verb (SpanAnnotation)
- `obj`: Object entity (SpanAnnotation)
- `context`: Optional sentence context (AnnotationContext)

Extractors expose two batch methods. `batch_extract` yields one result list per document
in input order. `batch_extract_unordered` yields `(index, triplets)` pairs instead, where
`index` is the document's position in the input, and makes no promise about the order
they arrive in. `Pipeline` consumes the latter, so a backend that finishes documents out
of order — as an LLM backend does — has its annotations stored the moment each document
comes back, rather than being held up behind a slower one. The default implementation
delegates to `batch_extract`, so extractors that do not override it stay ordered and
keep working unchanged.

### Cooccurrence Extraction (`tuplets/`)

| Class                             | Description                           |
| --------------------------------- | ------------------------------------- |
| **CooccurrenceExtractor**         | Abstract base class                   |
| **ChunkCooccurrenceExtractor**    | Sentence-based windowed cooccurrences |
| **DocumentCooccurrenceExtractor** | All entity pairs within a document    |

`ChunkCooccurrenceExtractor` features:

- Configurable sentence window size
- Custom boundary patterns (regex or callable)
- Sentence-level context capture

Tuplets consist of:

- `entity_one`, `entity_two`: Entity pair (SpanAnnotation)
- `context`: Optional context window (AnnotationContext)

## Mapping Components (`mapping/`)

Mappers normalize surface forms to canonical labels, creating a `dict[str, str]` mapping.

| Class                          | Description                                |
| ------------------------------ | ------------------------------------------ |
| **Mapper**                     | Abstract base class                        |
| **StemmingMapper**             | Groups by Porter stemmed form              |
| **SubgramStemmingMapper**      | Stemming + subgram matching for head words |
| **SubgramLemmatizationMapper** | Lemma + subgram matching for head words    |

`SubgramLemmatizationMapper` (default):

- First applies lemma normalization
- Then matches shorter forms to longer ones containing them
- Configurable for nouns or verbs via `head_word_type`
- Ranking by shortest label or most frequent

## LLM-Based Components

Where the rule-based components derive relations from the dependency parse, the LLM-based
ones take a plain-language instruction stating what to extract:

```python
from narrativegraphs.nlp.triplets import LlmTripletExtractor

extractor = LlmTripletExtractor(
    "Extract relations between characters and the places they travel to."
)
pipeline = Pipeline(engine, triplet_extractor=extractor)
```

They require the optional `anthropic` dependency:

```bash
pip install "narrativegraphs[llm-anthropic]"
```

and credentials in the environment (`ANTHROPIC_API_KEY`), or a pre-configured
`anthropic.Anthropic` instance passed as `client`.

### Span alignment

The rest of the package addresses entities by their character offsets in the document,
but a model returns strings. Every returned surface form is therefore located in the
source text again (`common/llm.py`):

1. The quoted evidence sentence is located and becomes the search window as well as the
   triplet's `context`, so that a repeated entity is anchored in the sentence the model
   actually meant.
2. Within that window, the parts are matched in order — verbatim first, then
   case-insensitively, then allowing whitespace to differ — falling back to the whole
   document and to order-independent matching.
3. Triplets with a part that cannot be found, or with overlapping parts, are dropped.
   Hallucinated and paraphrased spans do not reach the database.

### Cost and robustness

- One request per document, `max_concurrent_requests` of them in flight at a time,
  each stored as it returns via `batch_extract_unordered`.
- Structured outputs (`output_config.format`) guarantee schema-valid JSON.
- The default `effort="low"` suits bounded extraction at corpus scale; raise it for
  instructions that call for genuine judgement.
- Refusals, truncated responses and transient failures skip the document with a warning;
  authentication and request errors raise, since every later document would hit them too.

## Supporting Components

### Common Utilities (`common/`)

| Module                     | Purpose                                                                |
| -------------------------- | ---------------------------------------------------------------------- |
| **annotation.py**          | Data models: `SpanAnnotation`, `AnnotationContext`                     |
| **spacy.py**               | spaCy utilities: model loading, batch size calculation, span filtering |
| **transformcategories.py** | Normalizes various category input formats                              |
| **llm.py**                 | LLM utilities: JSON requests, concurrency, span alignment              |

`SpanAnnotation` represents a text span with:

- `text`: Surface form
- `start_char`, `end_char`: Character offsets
- `normalized_text`: Optional lemma

### Filtering (`filtering/`)

| Class            | Description                                    |
| ---------------- | ---------------------------------------------- |
| **BigramFilter** | PMI-based bigram filtering for quality control |

`BigramFilter` can be used to filter out low-quality multi-word spans based on bigram co-occurrence statistics.

## Architecture Diagram

```
Pipeline / CooccurrencePipeline
    │
    ├── Document ingestion
    │
    ├── Extraction
    │   ├── TripletExtractor ──► Triplet (subj, pred, obj)
    │   │   └── DependencyGraphExtractor (spaCy)
    │   │
    │   ├── EntityExtractor ──► SpanAnnotation
    │   │   └── SpacyEntityExtractor (NER + noun chunks)
    │   │
    │   └── CooccurrenceExtractor ──► Tuplet (entity_one, entity_two)
    │       ├── ChunkCooccurrenceExtractor (sentence window)
    │       └── DocumentCooccurrenceExtractor (all pairs)
    │
    ├── Mapping
    │   └── Mapper ──► dict[str, str]
    │       ├── StemmingMapper
    │       ├── LemmatizationMapper
    │       └── SubgramStemmingMapper (default)
    │       └── SubgramLemmatizationMapper
    │
    └── Stats calculation (via service layer)
```

## Extensibility

All extraction and mapping components use abstract base classes, making it easy to implement custom:

- Entity extractors (e.g., domain-specific NER)
- Triplet extractors (e.g., rule-based, LLM-based)
- Cooccurrence extractors (e.g., paragraph-level, custom boundaries)
- Mappers (e.g., embedding-based clustering, knowledge base linking)
