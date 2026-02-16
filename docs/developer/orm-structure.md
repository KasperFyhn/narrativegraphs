# ORM Structure

This guide provides an overview of the ORM structure in `narrativegraphs/db/`.

## Core Concepts

The data model supports two graph paradigms:

| Graph Type            | Primary Annotations                 | Has Relations/Predicates |
| --------------------- | ----------------------------------- | ------------------------ |
| **NarrativeGraph**    | Triplets (subject-predicate-object) | Yes                      |
| **CooccurrenceGraph** | Tuplets (entity-entity pairs)       | No                       |

## Annotation Types

Annotation ORMs store text extractions and have a direct `doc_id` reference.

### TripletOrm (`triplets.py`)

Represents a subject-predicate-object extraction from text.

- Has: `doc_id`, `subject_id`, `predicate_id`, `object_id`, `relation_id`, `cooccurrence_id`
- Stores span positions and text for subject, predicate, and object
- Mixes in `AnnotationMixin` (provides `doc_id`, `timestamp`, `document` relationship)

### TupletOrm (`tuplets.py`)

Represents an entity-entity cooccurrence extraction.

- Has: `doc_id`, `entity_one_id`, `entity_two_id`, `cooccurrence_id`
- Stores span positions and text for both entities
- Mixes in `AnnotationMixin`

### EntityOccurrenceOrm (`entityoccurrences.py`)

Represents a single entity mention/occurrence in text.

- Has: `doc_id`, `entity_id`, `span_start`, `span_end`, `span_text`
- Relationships: `entity` (→ EntityOrm), `document` (→ DocumentOrm)
- Mixes in `AnnotationMixin`
- Used by EntityOrm to derive `alt_labels` (alternative surface forms)

## Higher-Level ORMs

These ORMs represent canonical/deduplicated concepts backed by annotations. All mix in `AnnotationBackedTextStatsMixin` which provides:

- Stats columns: `frequency`, `doc_frequency`, `spread`, `adjusted_tf_idf`, `first_occurrence`, `last_occurrence`
- `_annotations` property (abstract, returns backing triplets/tuplets)
- `doc_ids` property (derived from `_annotations`)

### EntityOrm (`entities.py`)

Canonical entity (e.g., "Microsoft", "Satya Nadella").

- Relationships:
  - `occurrences` → EntityOccurrenceOrm (all mentions of this entity)
  - `subject_triplets` / `object_triplets` → `triplets` property
  - `_entity_one_tuplets` / `_entity_two_tuplets` → `tuplets` property
  - `subject_relations` / `object_relations` → `relations` property
  - `_entity_one_cooccurrences` / `_entity_two_cooccurrences` → `cooccurrences` property
- `_annotations` returns `triplets + tuplets` (union for both graph types)
- Has `alt_labels` hybrid property (derived from `occurrences` span texts)

### PredicateOrm (`predicates.py`)

Canonical predicate/verb (e.g., "acquired", "announced").

- Relationships: `triplets`, `relations`
- `_annotations` returns `triplets`
- Has `alt_labels` hybrid property

### RelationOrm (`relations.py`)

Canonical relation tuple: (subject_entity, predicate, object_entity).

- Has: `subject_id`, `predicate_id`, `object_id`, `significance`
- Relationships: `subject`, `predicate`, `object`, `triplets`
- `_annotations` returns `triplets`
- Has `alt_labels` hybrid property

### CooccurrenceOrm (`cooccurrences.py`)

Canonical cooccurrence: (entity_one, entity_two) where `entity_one_id <= entity_two_id`.

- Has: `entity_one_id`, `entity_two_id`, `pmi`
- Relationships: `entity_one`, `entity_two`, `tuplets`
- `_annotations` returns `tuplets`

## DocumentOrm (`documents.py`)

Source document with `text`, `str_id`, `timestamp`.

- Relationships: `triplets`, `tuplets`, `entity_occurrences`
- Has categories via `CategorizableMixin`

## Mixins (`common.py`, `documents.py`)

| Mixin                              | Purpose                                                           |
| ---------------------------------- | ----------------------------------------------------------------- |
| **CategorizableMixin**             | Provides category support                                         |
| **CategoryMixin**                  | Base for category tables (e.g., `EntityCategory`)                 |
| **HasAltLabels**                   | For ORMs with alternative surface forms                           |
| **AnnotationMixin**                | For triplets/tuplets (provides `doc_id`, `document` relationship) |
| **AnnotationBackedTextStatsMixin** | For higher-level ORMs (stats + `doc_ids`)                         |

## Relationship Diagram

```
DocumentOrm
    │
    ├── triplets ──────────► TripletOrm ◄── subject/object ── EntityOrm
    │                            │                              │
    │                            ├── predicate ── PredicateOrm  │
    │                            │                    │         │
    │                            └── relation ─── RelationOrm ◄─┘
    │                                                │
    ├── tuplets ────────────► TupletOrm ◄────────────┼── entity_one/two ── EntityOrm
    │                            │                   │
    │                            └── cooccurrence ── CooccurrenceOrm
    │
    └── entity_occurrences ─► EntityOccurrenceOrm ◄── entity ── EntityOrm
```
