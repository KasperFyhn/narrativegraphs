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
- **DependencyGraphExtractor** - Verb-first traversal; fine-grained boolean flags per relation type; no sentence-length limits
- **EntityPairExtractor** - Entity-pair traversal; declarative `PathPattern` list; supports compound "verb prep" predicates; guards: `max_sentence_length=60`, `max_entity_distance=10`
- **LlmTripletExtractor** - Prompts an LLM (Claude by default) with a plain-language instruction; returned surface forms are aligned back to character offsets, unlocatable ones dropped
- **LlmBatchTripletExtractor** - Same via the Message Batches API at half the price; `submit()` returns batch IDs, `collect()` redeems them later into one list per document (results live 29 days)

### Cooccurrence Extraction (`tuplets/`)

- **CooccurrenceExtractor** - Abstract base class
- **ChunkCooccurrenceExtractor** - Sentence-windowed cooccurrences (default)
- **DocumentCooccurrenceExtractor** - All entity pairs in document

## Batch Contracts

- **batch_extract** - yields one result list per document, in input order; the only batch
  method, and what `Pipeline` zips with its documents. A backend that finishes out of
  order reorders internally.
- Pre-computed annotations are the way around a long wait: `Pipeline.run(annotations=)` /
  `NarrativeGraph.fit(triplets=)` take one list per document instead of running the
  extractor.

## LLM Clients (`common/llm/`)

Three layers: pipeline components -> `LlmClient` (provider-agnostic interface) ->
implementations. Components never know which provider answers.

- **LlmClient** - `request_json(system_prompt, user_prompt, schema)`; the whole contract
- **BatchLlmClient** - narrower, adds async batching; only `AnthropicClient` implements it
- **AnthropicClient** - Claude (default); structured outputs, `effort`, prompt caching, batches
- **OpenAiCompatibleClient** - OpenAI, LM Studio, Ollama, vLLM via `base_url`;
  `response_format` JSON schema, `temperature`, strips code fences from sloppy local models

## Mentions (`common/mentions.py`)

- **find_all_occurrences** - every occurrence of a surface form; case-insensitive,
  whitespace-tolerant, word-boundary respecting
- **expand_to_all_occurrences** - adds the mentions an extractor did not report, keeping
  its own spans exactly (population resolves triplets by span). Always applied by
  `Pipeline`: extractors report only the entities of the relations they found, and
  generative models consolidate repeated relations, so mention counts would otherwise
  understate the text. Does not yet cover pronouns; that needs coreference resolution.

## Pre-computed Annotations

`Pipeline.run(annotations=...)`, `NarrativeGraph.fit(triplets=...)` and
`CooccurrenceGraph.fit(entities=...)` accept one annotation list per document and skip
extraction. Used for batch runs collected later, and for reusing one extraction across
several fits.

## Mapping (`mapping/`)

Maps surface forms to canonical labels: `dict[str, str]`

- **Mapper** - Abstract base class
- **StemmingMapper** - Groups by Porter stemmed form
- **SubgramStemmingMapper** - Stemming + subgram matching
- **SubgramLemmatizationMapper** - Lemmatization + subgram matching (default)

## LLM Support (`common/llm.py`)

- **LlmJsonClient** - Schema-constrained JSON requests to Claude
- **align_span / align_sequence** - Locate model-returned surface forms in the source text
- **map_ordered** - Order-preserving concurrent map for I/O-bound per-document requests

## spaCy Model Loading (`common/spacy.py`)

- **ensure_spacy_model** - the single entry point; pipelines from the same model share one
  `Vocab` (~83 MB -> ~30 MB for a NarrativeGraph). Each call still returns its own mutable
  `Language`, because call sites reconfigure pipelines incompatibly (extractor needs the
  parser, normalizer disables it) - which is why spaCy itself does not cache models.
- **clear_shared_vocabs** - drops the cache; for test isolation only

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

- `DependencyGraphExtractor` (triplets, default; `EntityPairDependencyExtractor` is an alternative)
- `ChunkCooccurrenceExtractor` (cooccurrences)
- `SubgramLemmatizationMapper("noun")` (entities)
- `SubgramLemmatizationMapper("verb")` (predicates)

**CooccurrencePipeline:**

- `SpacyEntityExtractor` (entities)
- `ChunkCooccurrenceExtractor` (cooccurrences)
- `SubgramLemmatizationMapper("noun")` (entities)
