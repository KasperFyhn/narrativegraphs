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

- Triplet extraction: `DependencyGraphExtractor`
- Cooccurrence extraction: `ChunkCooccurrenceExtractor`
- Entity mapping: `SubgramStemmingMapper("noun")`
- Predicate mapping: `SubgramStemmingMapper("verb")`

### CooccurrencePipeline

Uses an `EntityExtractor` directly to find entities, then extracts cooccurrences between them. Skips triplet extraction entirely.

Default components:

- Entity extraction: `SpacyEntityExtractor`
- Cooccurrence extraction: `ChunkCooccurrenceExtractor`
- Entity mapping: `SubgramStemmingMapper("noun")`

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

| Class                        | Description                                    |
| ---------------------------- | ---------------------------------------------- |
| **TripletExtractor**         | Abstract base class                            |
| **DependencyGraphExtractor** | Extracts triplets from spaCy dependency parses |

Triplets consist of:

- `subj`: Subject entity (SpanAnnotation)
- `pred`: Predicate/verb (SpanAnnotation)
- `obj`: Object entity (SpanAnnotation)
- `context`: Optional sentence context (AnnotationContext)

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

| Class                     | Description                                |
| ------------------------- | ------------------------------------------ |
| **Mapper**                | Abstract base class                        |
| **StemmingMapper**        | Groups by Porter stemmed form              |
| **SubgramStemmingMapper** | Stemming + subgram matching for head words |

`SubgramStemmingMapper` (default):

- First applies stemming normalization
- Then matches shorter forms to longer ones containing them
- Configurable for nouns or verbs via `head_word_type`
- Ranking by shortest label or most frequent

## Supporting Components

### Common Utilities (`common/`)

| Module                     | Purpose                                                                |
| -------------------------- | ---------------------------------------------------------------------- |
| **annotation.py**          | Data models: `SpanAnnotation`, `AnnotationContext`                     |
| **spacy.py**               | spaCy utilities: model loading, batch size calculation, span filtering |
| **transformcategories.py** | Normalizes various category input formats                              |

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
    │       └── SubgramStemmingMapper (default)
    │
    └── Stats calculation (via service layer)
```

## Extensibility

All extraction and mapping components use abstract base classes, making it easy to implement custom:

- Entity extractors (e.g., domain-specific NER)
- Triplet extractors (e.g., rule-based, LLM-based)
- Cooccurrence extractors (e.g., paragraph-level, custom boundaries)
- Mappers (e.g., embedding-based clustering, knowledge base linking)
