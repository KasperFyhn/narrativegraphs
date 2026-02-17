---
name: nlp-guide
description: Overview of the NLP layer for text extraction and mapping
user-invocable: false
---

# NLP Layer Guide

Overview of the NLP layer in `narrativegraphs/nlp/`.

## Pipelines

| Pipeline                 | Purpose                                         |
| ------------------------ | ----------------------------------------------- |
| **Pipeline**             | Full narrative graph (triplets + cooccurrences) |
| **CooccurrencePipeline** | Simpler cooccurrence-only extraction            |

Both handle: document ingestion → extraction → mapping → stats calculation.

## Extraction Components

### Entity Extraction (`entities/`)

- **EntityExtractor** - Abstract base class
- **SpacyEntityExtractor** - NER + noun chunks with length filtering, non-overlapping selection

### Triplet Extraction (`triplets/`)

- **TripletExtractor** - Abstract base class
- **DependencyGraphExtractor** - Extracts (subject, predicate, object) from dependency parses

### Cooccurrence Extraction (`tuplets/`)

- **CooccurrenceExtractor** - Abstract base class
- **ChunkCooccurrenceExtractor** - Sentence-windowed cooccurrences (default)
- **DocumentCooccurrenceExtractor** - All entity pairs in document

## Mapping (`mapping/`)

Maps surface forms to canonical labels: `dict[str, str]`

- **Mapper** - Abstract base class
- **StemmingMapper** - Groups by Porter stemmed form
- **SubgramStemmingMapper** - Stemming + subgram matching (default)

## Data Models (`common/`)

- **SpanAnnotation** - Text span with offsets (`text`, `start_char`, `end_char`)
- **AnnotationContext** - Context window (`text`, `doc_offset`)
- **Triplet** - `subj`, `pred`, `obj` (SpanAnnotation) + optional `context`
- **Tuplet** - `entity_one`, `entity_two` (SpanAnnotation) + optional `context`

## Architecture

```
Pipeline / CooccurrencePipeline
    │
    ├── TripletExtractor → Triplet
    ├── EntityExtractor → SpanAnnotation
    ├── CooccurrenceExtractor → Tuplet
    └── Mapper → canonical labels
```

## Default Components

**Pipeline:**

- `DependencyGraphExtractor` (triplets)
- `ChunkCooccurrenceExtractor` (cooccurrences)
- `SubgramStemmingMapper("noun")` (entities)
- `SubgramStemmingMapper("verb")` (predicates)

**CooccurrencePipeline:**

- `SpacyEntityExtractor` (entities)
- `ChunkCooccurrenceExtractor` (cooccurrences)
- `SubgramStemmingMapper("noun")` (entities)
