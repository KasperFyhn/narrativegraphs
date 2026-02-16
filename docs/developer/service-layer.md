# Service Layer

This guide provides an overview of the service layer in `narrativegraphs/service/`.

## Core Services

The service layer has two main entry points:

| Service               | Purpose                                                   |
| --------------------- | --------------------------------------------------------- |
| **QueryService**      | Read/query operations on the database                     |
| **PopulationService** | Write operations (adding documents, annotations, mapping) |

Both extend `DbService` which provides thread-safe session management via `get_session_context()`.

## QueryService

Main entry point for reading data. Composes sub-services for each entity type:

| Sub-service     | Entity Type      | Key Capabilities                                     |
| --------------- | ---------------- | ---------------------------------------------------- |
| `documents`     | DocumentOrm      | Retrieve docs with optional eager-loaded annotations |
| `entities`      | EntityOrm        | Search, lookup, get associated doc IDs               |
| `relations`     | RelationOrm      | Query relations between entities                     |
| `predicates`    | PredicateOrm     | Query predicates                                     |
| `cooccurrences` | CooccurrenceOrm  | Query cooccurrences between entities                 |
| `triplets`      | TripletOrm       | Query triplet annotations                            |
| `tuplets`       | TupletOrm        | Query tuplet annotations                             |
| `graph`         | Graph operations | Subgraph extraction, expansion, community detection  |

All sub-services extend `OrmAssociatedService` and provide standard methods for DataFrame export, single/multiple record retrieval, plus entity-specific queries.

## PopulationService

Main entry point for populating the database. Handles:

1. **Document ingestion** - Bulk insert documents with metadata (IDs, timestamps, categories)

2. **Annotation ingestion** (two-phase):

   - First add entity occurrences, get a lookup dict
   - Then add triplets/tuplets referencing occurrences via the lookup

3. **Mapping to canonical entities** - Map annotations to deduplicated entities, predicates, relations, and cooccurrences using provided mapping dictionaries

## Supporting Services

### StatsCalculator (`stats.py`)

Computes aggregate statistics after population is complete:

- Entity/predicate/relation/cooccurrence frequency and doc_frequency
- Spread, adjusted TF-IDF, first/last occurrence timestamps
- Relation significance scores
- Cooccurrence PMI values
- Category propagation from documents to higher-level entities

### GraphService (`graph.py`)

Specialized service for graph operations:

- **Subgraph extraction** - Get graph for specific entity IDs
- **Expansion** - Expand from focus entities to connected neighbors
- **Community detection** - Louvain, k-clique, or connected components algorithms

Supports two connection types: `"relation"` (directed, with predicates) and `"cooccurrence"` (undirected pairs).

### Caches (`cache.py`)

Used internally by `PopulationService` for efficient bulk mapping:

| Cache                 | Purpose                                      |
| --------------------- | -------------------------------------------- |
| **EntityCache**       | Maps surface forms to canonical entities     |
| **PredicateCache**    | Maps predicate texts to canonical predicates |
| **CooccurrenceCache** | Creates/retrieves cooccurrence pairs         |
| **RelationCache**     | Creates/retrieves relation triples           |

### Filter Functions (`filter.py`)

Builds SQLAlchemy conditions for graph queries. Supports filtering by:

- Date range (first/last occurrence)
- Frequency and doc_frequency bounds
- Categories
- Entity blacklist

## Base Classes (`common.py`)

| Class                    | Purpose                                                                                   |
| ------------------------ | ----------------------------------------------------------------------------------------- |
| **DbService**            | Thread-safe session management                                                            |
| **SubService**           | Base for services sharing session context                                                 |
| **OrmAssociatedService** | Base for services tied to a specific ORM (provides `as_df`, `get_single`, `get_multiple`) |

## Architecture Diagram

```
QueryService (read)                    PopulationService (write)
    │                                          │
    ├── documents                              ├── add documents
    ├── entities                               ├── add entity occurrences
    ├── relations                              ├── add triplets / tuplets
    ├── predicates                             └── map to canonical entities
    ├── cooccurrences                                  │
    ├── triplets                                       └── Uses Caches
    ├── tuplets                                            ├── EntityCache
    └── graph ─────────────────┐                           ├── PredicateCache
                               │                           ├── CooccurrenceCache
                               └── Uses filter.py          └── RelationCache

                           StatsCalculator
                                │
                                └── calculate_stats() after population
```
