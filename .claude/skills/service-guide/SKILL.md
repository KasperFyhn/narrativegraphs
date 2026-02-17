---
name: service-guide
description: Overview of the service layer architecture and usage
user-invocable: false
---

# Service Layer Guide

Overview of the service layer in `narrativegraphs/service/`.

## Core Services

| Service               | Purpose                                                       |
| --------------------- | ------------------------------------------------------------- |
| **QueryService**      | Read/query operations (documents, entities, relations, graph) |
| **PopulationService** | Write operations (adding docs, annotations, mapping)          |

Both extend `DbService` which provides thread-safe session management.

## QueryService

Composes sub-services for each entity type:

- `documents` - DocService for DocumentOrm
- `entities` - EntityService for EntityOrm (includes search)
- `relations` - RelationService for RelationOrm
- `predicates` - PredicateService for PredicateOrm
- `cooccurrences` - CooccurrenceService for CooccurrenceOrm
- `triplets` - TripletService for TripletOrm
- `tuplets` - TupletService for TupletOrm
- `graph` - GraphService for graph operations

All sub-services provide: DataFrame export, single/multiple record retrieval, plus entity-specific queries.

## PopulationService

1. **Document ingestion** - Bulk insert with metadata
2. **Annotation ingestion** - Add entity occurrences first, then triplets/tuplets
3. **Mapping** - Map annotations to canonical entities/predicates/relations/cooccurrences

## Supporting Services

### StatsCalculator (`stats.py`)

Computes aggregate statistics after population: frequency, doc_frequency, spread, TF-IDF, timestamps, relation significance, cooccurrence PMI, category propagation.

### GraphService (`graph.py`)

Graph operations: subgraph extraction, expansion from focus entities, community detection (louvain, k_clique, connected_components). Supports `"relation"` and `"cooccurrence"` connection types.

### Caches (`cache.py`)

Used by PopulationService for efficient bulk mapping: EntityCache, PredicateCache, CooccurrenceCache, RelationCache.

### Filter Functions (`filter.py`)

Builds SQLAlchemy conditions for graph queries: date range, frequency bounds, categories, blacklist.

## Architecture

```
QueryService (read)                    PopulationService (write)
    │                                          │
    ├── sub-services per entity type           ├── add documents/annotations
    └── graph (GraphService)                   └── map to canonical (uses Caches)
            │
            └── filter.py conditions

                    StatsCalculator.calculate_stats() after population
```
