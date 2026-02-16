---
name: visualizer-guide
description: Overview of the React frontend for graph visualization
user-invocable: false
---

# Visualizer Frontend Guide

Overview of the visualizer in `visualizer/`.

## Overview

React/TypeScript SPA for interactive graph visualization. Uses react-graph-vis for rendering.

## Structure

```
src/
├── components/   # React components (graph/, inspector/, common/)
├── contexts/     # State providers (Service, GraphQuery, GraphOptions, Selection)
├── hooks/        # Custom hooks
├── reducers/     # State reducers (filter, query, history)
├── services/     # API clients (Graph, Doc, Entity, Relation, Cooccurrence)
└── types/        # TypeScript definitions
```

## Context Hierarchy

```
ServiceContext (API services)
  └── GraphOptionsContext (viz options)
      └── GraphQueryContext (query state)
          └── SelectionContext (selected items)
```

## Services

Mirror backend routes with auto-detected API URL:

- GraphService → `/graph`
- DocService → `/docs`
- EntityService → `/entities`
- RelationService → `/relations`
- CooccurrenceService → `/cooccurrences`

## Development

```bash
npm install
npm start      # Dev server :3000, proxies to :8001
npm run build  # Output to build/
```

Build output is served by the FastAPI backend from `server/static/`.
